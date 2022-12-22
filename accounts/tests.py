from datetime import datetime
from django.core import mail
from django.test import TestCase
from django_q.tasks import Schedule
from django.core.management import call_command
from .models import CustomUser, Profile, Subscription
from .tasks import *

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
        Profile.objects.create(user=user, subscription=subscription)
    
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