from interlab import test_utils

import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group
from accounts.models import CustomUser
from openings.models import Opening
from fabcal.forms import OpeningSlotForm
from fabcal.models import OpeningSlot
from machines.models import Machine

# Create your tests here.
class TestOpeningSlotCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('fabcal:openingslot-create') + '?start=1682784000000&end=1682791200000'
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass',
            email='user@fake.django'
            )
        self.superuser = CustomUser.objects.create_user(
            username='testsuperuser',
            password='testpass',
            email='superuser@fake.django'
            )
        self.group = Group.objects.get_or_create(name='superuser')[0]
        self.superuser.groups.add(self.group)
        self.openlab = Opening.objects.create(
            title='OpenLab', 
            is_open_to_reservation=True, 
            is_open_to_questions=True,
            is_reservation_mandatory=False,
            is_public=True
            )
        self.trotec = Machine.objects.create(
            title = 'Trotec'
        )
        self.prusa = Machine.objects.create(
            title = 'Prusa'
        )

    def test_authenticated_user_can_access(self):
        self.client.login(username='testuser', password='testpass')

        # Test if user is not in superuser group
        self.assertFalse(self.user.groups.filter(name='superuser').exists())

        # Assert view-specific content
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)

        # Assert view-specific content
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_superuser_in_superuser_group(self):
        self.client.login(username='testsuperuser', password='testpass')
        # Test if user is in group
        self.assertTrue(self.superuser.groups.filter(name='superuser').exists())

        # Assert view-specific content
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_form_valid(self):
        form_data = {
            'opening': self.openlab.id,
            'machines': [self.trotec.id],
            'date': '1 mai 2023',
            'start_time': '10:00',
            'end_time': '12:00',
            'comment': 'my comment'
        }
        form = OpeningSlotForm(form_data)
        self.assertTrue(form.is_valid())

        # Check if the instance is of the correct class
        self.assertIsInstance(form.save(commit=False), OpeningSlot)

    def test_start_time_before_end_time(self):
        form_data = {
            'opening': self.openlab.id,
            'date': '2023-05-01',
            'start_time': '10:00',
            'end_time': '09:00',  # Invalid end time
            'comment': 'my comment'
        }
        form = OpeningSlotForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['__all__'][0].code, 'invalid_time_range')

    def test_overlaps(self):
        OpeningSlot.objects.all().delete()
        
        # Create a first opening
        form_data = {
            'opening': self.openlab.id,
            'machines': [self.trotec.id],
            'date': '1 mai 2023',
            'start_time': '10:00',
            'end_time': '12:00'
        }
        
        self.client.login(username='testsuperuser', password='testpass')
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 302)

        # Test exact overlap with a second opening
        form_data = {
            'opening': self.openlab.id,
            'machines': [self.trotec.id],
            'date': '1 mai 2023',
            'start_time': '10:00',
            'end_time': '12:00',
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')

        # Test second opening start before, and end during an existing opening
        form_data = {
            'opening': self.openlab.id,
            'date': '1 mai 2023',
            'start_time': '09:00',
            'end_time': '11:00',
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')

    def test_view_valid(self):
        self.client.login(username='testsuperuser', password='testpass')
        form_data = {
            'opening': self.openlab.id,
            'machines': [self.trotec.id],
            'date': '1 mai 2023',
            'start_time': '10:00',
            'end_time': '12:00',
            'comment': 'my comment'
        }

        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/schedule/', response.url)
        
        obj = OpeningSlot.objects.latest('id')
        self.assertEqual(obj.start, datetime.datetime(2023, 5, 1, 10, 0))
        self.assertEqual(obj.end, datetime.datetime(2023, 5, 1, 12, 0))
        self.assertEqual(obj.comment, 'my comment')
        self.assertEqual(obj.user, self.superuser)

        self.assertEqual(obj.get_machine_list, [self.trotec])

    def tearDown(self):
        self.client.logout()
        self.user.delete()
        self.superuser.delete()
        self.group.delete()
