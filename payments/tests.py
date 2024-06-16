from django.test import Client
from django.utils import timezone
from datetime import timedelta, date
from django.test import TestCase
from accounts.models import Profile, CustomUser, Subscription, SubscriptionCategory
from payments.views import fulfill_order

class SubscriptionRenewBase(TestCase):
    def __init__(self, methodName, start: date, end: date, with_subscription: bool):
        super().__init__(methodName)
        self.start = start
        self.end = end
        self.with_subscription = with_subscription

    def setUp(self):
        self.user = CustomUser.objects.create(email='someuser@fake.django')
        subscription = None
        category = SubscriptionCategory.objects.create(pk=1, duration=1000, price=1234, star_flag=False, sort=0, default_access_number=123)
        if self.with_subscription:
            subscription = Subscription.objects.create(pk=1, access_number=42, start=self.start, end=self.end, subscription_category=category)
        self.user.profile.subscription = subscription
        self.user.profile.save()

    def tearDown(self):
        super().tearDown()
        self.user.delete()

    def _test_renew_should_create_new_subscription(self, expected_duration, subscription_category_id):
        session = {'customer_details': {'email':'someuser@fake.django'}, 'metadata': {'profile_id': self.user.profile.id, 'subscription_category_id': subscription_category_id}}
        fulfill_order(session, None)

        profile = Profile.objects.get(user__email='someuser@fake.django')
        self.assertEqual(profile.subscription.end - profile.subscription.start, timedelta(days=expected_duration), 'should be valid until duration from now')
        self.assertEqual(Subscription.objects.count(), 2, 'should have created a new subscription')
        self.assertEqual(profile.subscription.start, timezone.now().date(), 'should always start from now')
        return profile

class UserWithoutSubscription(SubscriptionRenewBase):
    def __init__(self, methodName):
        now = timezone.now().date()
        super().__init__(
            methodName,
            start=now-timedelta(weeks=52), 
            end=now+timedelta(weeks=1),
            with_subscription=False
        )

    def test_user_without_subscription_should_get_default_subscription_category(self):
        session = {'customer_details': {'email':'someuser@fake.django'}, 'metadata': {'profile_id':self.user.profile.id, 'subscription_category_id': 1}}
        fulfill_order(session, None)
        self.assertEqual(Subscription.objects.count(), 1, 'should have created a new subscription')
        created_subscription = Subscription.objects.first()
        now = timezone.now().date()
        self.assertEqual(created_subscription.access_number, 123, 'should have reuse category access number')
        self.assertEqual(created_subscription.start, now, 'should start today')
        self.assertEqual(created_subscription.end, now + timedelta(days=1000), 'should end at duration from category')
        self.assertEqual(created_subscription.subscription_category.pk, 1, 'should have the expected category')

class SubscriptionRenewExpriringTestCase(SubscriptionRenewBase):
    
    def __init__(self, methodName):
        now = timezone.now().date()
        super().__init__(
            methodName,
            start=now-timedelta(weeks=52), 
            end=now+timedelta(weeks=1),
            with_subscription=True
        )

    def test_renew_should_create_new_subscription(self):
        self._test_renew_should_create_new_subscription(expected_duration=1007, subscription_category_id=1)


class SubscriptionRenewAlternateCategoryTestCase(SubscriptionRenewBase):
    
    def __init__(self, methodName):
        now = timezone.now().date()
        super().__init__(
            methodName,
            start=now-timedelta(weeks=52), 
            end=now+timedelta(weeks=1),
            with_subscription=True
        )

    def setUp(self):
        super().setUp()
        SubscriptionCategory.objects.create(pk=2, duration=500, price=333, star_flag=True, sort=1, default_access_number=1)

    def test_renew_should_create_new_subscription(self):
        self._test_renew_should_create_new_subscription(expected_duration=500, subscription_category_id=2)

class SubscriptionRenewExpiredTestCase(SubscriptionRenewBase):
    
    def __init__(self, methodName):
        now = timezone.now().date()
        super().__init__(
            methodName,
            start=now-timedelta(weeks=52), 
            end=now-timedelta(weeks=1),
            with_subscription=True
        )

    def test_renew_should_create_new_subscription(self):
        self._test_renew_should_create_new_subscription(expected_duration=1000, subscription_category_id=1)

class TestViewBase(TestCase):

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(username='alphonse', email='dontexists@django.fake', password='fonce')
        SubscriptionCategory.objects.create(title='title', price=12, sort=0, star_flag=False, default_access_number=1, duration=1)

    def tearDown(self):
        super().tearDown()
        self.user.delete()

class TestUpdateViews(TestViewBase):

    def _base_view_check(self, url):
        client = Client(enforce_csrf_checks=True)
        response = client.get(url)
        self.assertEqual(response.status_code, 302)
        result = client.login(username='alphonse', password='fonce')
        self.assertEqual(True, result)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        return response

    def test_update_view(self):
        response = self._base_view_check('/payments/subscription-update/')

    def test_update_product_view(self):
        response = self._base_view_check('/payments/subscription-update/product/1/')

    def test_update_cancel_view(self):
        response = self._base_view_check('/payments/subscription-update/cancel/')

    def test_update_success_view(self):
        response = self._base_view_check('/payments/subscription-update/success/')

class TestCreateSession(TestViewBase):

    def _login(self, enforce_csrf_checks):
        client = Client(enforce_csrf_checks=enforce_csrf_checks)
        result = client.login(username='alphonse', password='fonce')
        self.assertEqual(True, result)
        return client

    def test_direct_checkout_require_login(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post('/payments/create-checkout-session/1/')
        self.assertEqual(response.status_code, 403)

    def test_direct_checkout_redirect(self):
        client = self._login(enforce_csrf_checks=False)
        response = client.post('/payments/create-checkout-session/1/')
        self.assertRedirects(response, response.url, fetch_redirect_response=False)

    def test_form_checkout_require_csrf(self):
        client = self._login(enforce_csrf_checks=True)
        response = client.post('/payments/create-checkout-session/', { 'category_id': 1 })
        self.assertEqual(response.status_code, 403)

    def test_form_checkout_require_login(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post('/payments/create-checkout-session/', { 'category_id': 1 })
        self.assertEqual(response.status_code, 403)

    def test_form_checkout_redirect(self):
        client = self._login(enforce_csrf_checks=False)
        response = client.post('/payments/create-checkout-session/', { 'category_id': 1 })
        self.assertRedirects(response, response.url, fetch_redirect_response=False)

    def test_form_checkout_internal_redirect(self):
        client = self._login(enforce_csrf_checks=False)
        response = client.post('/payments/create-checkout-session/', { })
        self.assertRedirects(response, '/payments/subscription-update/')
        