from django.utils import timezone
from datetime import timedelta, date
from django.test import TestCase
from accounts.models import Profile, CustomUser, Subscription, SubscriptionCategory

from .views import fulfill_order

class SubscriptionRenewBase(TestCase):
    def __init__(self, methodName, start: date, end: date, with_subscription: bool):
        super().__init__(methodName)
        self.start = start
        self.end = end
        self.with_subscription = with_subscription

    def setUp(self):
        user = CustomUser.objects.create(email='someuser@fake.django')
        subscription = None
        category = SubscriptionCategory.objects.create(pk=1, duration=1000, price=1234, star_flag=False, sort=0, default_access_number=123)
        if self.with_subscription:
            subscription = Subscription.objects.create(pk=1, access_number=42, start=self.start, end=self.end, subscription_category=category)
        Profile.objects.create(pk=12, user=user, subscription=subscription)

    def _test_renew_should_create_new_subscription(self):
        session = {'customer_details': {'email':'someuser@fake.django'}, 'metadata': {'profile_id': 12, 'subscription_category_id': 1}}
        fulfill_order(session, None)

        profile = Profile.objects.get(user__email='someuser@fake.django')
        self.assertEqual(profile.subscription.end - profile.subscription.start, timedelta(days=1000), 'should be valid until duration from now')
        self.assertEqual(Subscription.objects.count(), 2, 'should have created a new subscription')
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

    def test_user_without_user_should_get_default_subscription_category(self):
        session = {'customer_details': {'email':'someuser@fake.django'}, 'metadata': {'profile_id':12, 'subscription_category_id': 1}}
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
        profile = self._test_renew_should_create_new_subscription()
        now = timezone.now().date()
        self.assertEqual(profile.subscription.start, now+timedelta(weeks=1), 'not expired yet, should start at the end of the original subscription')
        


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
        self._test_renew_should_create_new_subscription()

    
        

