from django.contrib.auth.models import Group
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from interlab import test_utils

from datetime import datetime
from django.core import mail
from django.test import TestCase, RequestFactory
from django_q.tasks import Schedule
from django.core.management import call_command
from .models import CustomUser, Profile, Subscription
from .tasks import *
from .views import UserListView, SuperuserProfileEditView


class SuperuserRequiredTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.login_url = reverse('accounts:login')

        # Create a superuser and add them to the 'superuser' group
        self.superuser = CustomUser.objects.create_superuser(username='admin', password='adminpassword',
                                                             email='admin@exmple.test')
        self.superuser_group = Group.objects.create(name='superuser')
        self.superuser.groups.add(self.superuser_group)

        # Create a non-superuser and add them to the 'normal' group
        self.user = CustomUser.objects.create_user(username='user', password='userpassword', email='user@exmple.test')
        self.normal_group = Group.objects.create(name='normal')
        self.user.groups.add(self.normal_group)

    def tearDown(self):
        super().tearDown()
        self.superuser.delete()
        self.superuser_group.delete()
        self.user.delete()
        self.normal_group.delete()

class ExpiredAndReminderTestCase(TestCase):
    def setUp(self):
        for i in range(-8, 9): # 17 subscriptions 8 before and a 8 after
            self.create_subscription("test{}_{}@mail.django".format(i, 'neg' if i < 0 else 'pos'), timedelta(days=i))

    def assert_single_mail_and_result(self, email, result):
        self.assertNotEqual(result, None)
        self.assertEqual(len(result), 1, 'should return user list')
        self.assertEqual(len(mail.outbox), 1, 'should have sent an email')
        self.assertTrue(email in mail.outbox[0].to)

    def create_subscription(self, email: str, delta: timedelta):
        user = CustomUser.objects.create(username=email.replace('@', '_'), email=email)
        subscription = Subscription.objects.create(start=datetime.today(), end=datetime.today() + delta, access_number=0)
        user.profile.subscription = subscription
        user.profile.save()
    
    def test_expire_only_the_target_day(self):
        result = send_expire_subscription_email()
        self.assert_single_mail_and_result('test0_pos@mail.django', result)
        
    def test_reminder_only_a_week_before(self):
        result = send_reminder_subscription_email()
        self.assert_single_mail_and_result('test7_pos@mail.django', result)

class ExpiredAndReminderCommandsTestCase(TestCase):
    def test_createtasks_command(self):
        call_command('createtasks')
        reminder = Schedule.objects.get(name='Accounts.Reminder', func='accounts.tasks.send_reminder_subscription_email')
        self.assertIsNotNone(reminder, 'should have been created on startup')
        self.assertEqual(reminder.schedule_type, Schedule.DAILY, 'should be daily scheduled')
        expired = Schedule.objects.get(name='Accounts.Expired', func='accounts.tasks.send_expire_subscription_email')
        self.assertIsNotNone(expired, 'should have been created on startup')
        self.assertEqual(expired.schedule_type, Schedule.DAILY, 'should be daily scheduled')


class SuperUserRequiredMixinsTestCases(SuperuserRequiredTestCase):
    def userlist_view(self, user):
        request = self.factory.get('/')
        request.user = user
        return UserListView.as_view(template_name='accounts/blank.html'), request

    def test_userlist_is_denied_for_normal_user(self):
        view, request = self.userlist_view(self.user)
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_userlist_is_allowed_for_superuser(self):
        view, request = self.userlist_view(self.superuser)
        response = view(request)
        self.assertEqual(200, response.status_code)

    def test_userlist_filter_is_denied_for_normal_user(self):
        view, request = self.userlist_view(self.user)
        with self.assertRaises(PermissionDenied):
            view(request, search='*')

    def test_userlist_filter_is_allowed_for_superuser(self):
        view, request = self.userlist_view(self.superuser)
        response = view(request, search='*')
        self.assertEqual(200, response.status_code)

    def superuser_profile_view(self, user):
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        request.user = user
        return SuperuserProfileEditView.as_view(template_name='accounts/blank.html'), request

    def test_superuser_profile_get_is_denied_for_normal_user(self):
        view, request = self.superuser_profile_view(self.user)
        with self.assertRaises(PermissionDenied):
            view(request, pk=self.user.id)

    def test_superuser_profile_get_is_allowed_for_superuser(self):
        view, request = self.superuser_profile_view(self.superuser)
        response = view(request, pk=self.user.id)
        self.assertEqual(200, response.status_code)
