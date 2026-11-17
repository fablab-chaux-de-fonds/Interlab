import datetime
from unittest import TestCase

from django.core.exceptions import PermissionDenied

from accounts.tests import SuperuserRequiredTestCase
from fabcal.models import TrainingSlot
from machines.models import Training, MachineCategory
from machines.templatetags.training_extras import price_format
from machines.views import TrainingValidationView


class PriceTests(TestCase):
    def test_price_format(self):
        self.assertEqual(price_format(12), "12 CHF")
        self.assertEqual(price_format(12.3), "12.30 CHF")
        self.assertEqual(price_format(12.34), "12.34 CHF")
        self.assertEqual(price_format(12.345), "12.35 CHF")
        self.assertEqual(price_format(4.321), "4.32 CHF")

class SuperUserRequiredMixinsTestCases(SuperuserRequiredTestCase):

    def setUp(self):
        super().setUp()
        self.category = MachineCategory.objects.create(name='Machine Category')
        self.training = Training.objects.create(
            machine_category=self.category,
            level=Training.BEGINNER,
            duration=datetime.timedelta(hours=1),
        )
        self.training_slot = TrainingSlot.objects.create(
            training=self.training,
            start=datetime.datetime(year=2021, month=1, day=1),
            end=datetime.datetime(year=2021, month=1, day=1),
        )

    def tearDown(self):
        super().tearDown()
        self.training_slot.delete()
        self.training.delete()
        self.category.delete()

    def training_validation_view(self, user):
        request = self.factory.get('/')
        request.user = user
        return TrainingValidationView.as_view(template_name='trainings/blank.html'), request

    def test_training_validation_is_denied_for_normal_users(self):
        view, request = self.training_validation_view(self.user)
        with self.assertRaises(PermissionDenied):
            view(request, pk=self.training_slot.id)

    def test_training_validation_is_allowed_for_superuser(self):
        view, request = self.training_validation_view(self.superuser)
        response = view(request, pk=self.training_slot.id)
        self.assertEqual(200, response.status_code)