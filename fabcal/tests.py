import datetime
import re

from unittest.mock import patch

from django.contrib.auth.mixins import LoginRequiredMixin 
from django.contrib.auth.models import Group, AnonymousUser
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.views import View

from accounts.models import CustomUser
from machines.models import Machine
from machines.models import MachineCategory
from machines.models import Training
from machines.models import TrainingValidation
from machines.models import TrainingNotification
from openings.models import Event
from openings.models import Opening

from .forms import OpeningSlotForm
from .forms import OpeningSlotCreateForm
from .forms import MachineSlotUpdateForm
from .forms import TrainingSlotCreateForm
from .forms import TrainingSlotUpdateForm
from .forms import TrainingSlotRegistrationCreateForm
from .forms import TrainingSlotRegistrationDeleteForm
from .forms import EventSlotCreateForm
from .forms import EventSlotUpdateForm
from .forms import EventSlotRegistrationCreateForm
from .forms import EventSlotRegistrationDeleteForm
from .mixins import SuperuserRequiredMixin
from .models import OpeningSlot
from .models import MachineSlot
from .models import TrainingSlot
from .models import EventSlot
from .views import OpeningSlotCreateView
from .views import OpeningSlotUpdateView
from .views import OpeningSlotDeleteView
from .views import MachineSlotUpdateView
from .views import MachineSlotDeleteView
from .views import TrainingSlotCreateView
from .views import TrainingSlotDeleteView
from .views import TrainingSlotRegistrationCreateView
from .views import TrainingSlotRegistrationDeleteView
from .views import EventSlotCreateView
from .views import EventSlotUpdateView
from .views import EventSlotDeleteView
from .views import EventSlotRegistrationCreateView
from .views import EventSlotRegistrationDeleteView

class TestView(SuperuserRequiredMixin, View):
    def get(self, request):
        self.request = request
        return HttpResponse('Success')

class SuperuserRequiredMixinTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.login_url = reverse('accounts:login')

    def test_superuser_required(self):
        # Create a superuser and add them to the 'superuser' group
        superuser = CustomUser.objects.create_superuser(username='admin', password='adminpassword')
        superuser_group = Group.objects.create(name='superuser')
        superuser.groups.add(superuser_group)

        # Create a request and set the user attribute to the superuser
        request = self.factory.get('/')
        request.user = superuser

        # Create an instance of the view and check if test_func returns True
        view = TestView()
        view.setup(request)
        self.assertTrue(view.test_func())

    def test_non_superuser_denied(self):
        # Create a non-superuser and add them to the 'normal' group
        user = CustomUser.objects.create_user(username='user', password='userpassword')
        normal_group = Group.objects.create(name='normal')
        user.groups.add(normal_group)

        # Create a request and set the user attribute to the non-superuser
        request = self.factory.get('/')
        request.user = user

        # Create an instance of the view and check if test_func returns False
        view = TestView.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_unauthenticated_redirect(self):
        # Create a request with an unauthenticated user
        request = self.factory.get('/')
        request.user = AnonymousUser()

        # Create an instance of the view and call handle_no_permission
        view = TestView.as_view()
        response = view(request)

        # Check that the response is a redirect to the login page with the next parameter
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

class SlotViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.create_url = reverse('fabcal:openingslot-create', kwargs=self.get_creation_url_parameter())

        self.user = CustomUser.objects.create_user(
            username='user',
            password='userpassword',
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

        self.laser_category = MachineCategory.objects.create(
            name = 'laser'
        )
        self.printer_category = MachineCategory.objects.create(
            name = '3D'
        )
        
        self.trotec = Machine.objects.create(
            title = 'Trotec',
            category = self.laser_category,
            photo = 'trotec.png',
            full_price = 20
        )
        self.prusa = Machine.objects.create(
            title = 'Prusa',
            category=self.printer_category
        )

        self.laser_training = Training.objects.create(
            title = 'laser',
            machine_category = self.laser_category,
            duration=datetime.timedelta(hours=1, minutes=30),
            photo = 'laser_training.png',
            full_price = 40
        )

        self.event = Event.objects.create(
            title = 'my event title',
            lead = 'my event lead',
            desc = 'my event description',
            img = 'event.png',
            is_active = True,
            is_on_site = True,
            location = 'Fablab'
        )

    def get_creation_url_parameter(self):
        return dict(
            start=1682935200000,
            end=1682942400000
        )

    def get_default_form_data(self, opening=None, machines=None, date=None, start_time=None, end_time=None, **kwargs):
        return {
            'opening': opening or self.openlab.id,
            'machines': machines or [self.trotec.id],
            'date': date or '1 mai 2023',
            'start_time': start_time or '10:00',
            'end_time': end_time or '12:00',
            'comment': 'my comment',
        }

    def create_opening_slot(self, **kwargs):
        self.client.login(username='testsuperuser', password='testpass')
        form_data = self.get_default_form_data(**kwargs)
        return self.client.post(self.create_url, form_data)

class OpeningSlotCreateViewTestCase(SlotViewTestCase):
    def setUp(self):
        super().setUp()

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(OpeningSlotCreateView, SuperuserRequiredMixin))

    def test_save_method(self):
        form = OpeningSlotCreateForm(data=self.get_default_form_data(), user=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        
        # Assertions for the instance attributes
        self.assertEqual(form.instance.user, self.user)
        self.assertEqual(form.instance.start, datetime.datetime.combine(datetime.date(2023, 5, 1), datetime.time(10, 0)))
        self.assertEqual(form.instance.end, datetime.datetime.combine(datetime.date(2023, 5, 1), datetime.time(12, 0)))

        # Assertions for related MachineSlot objects
        machine_slots = MachineSlot.objects.filter(opening_slot=form.instance)
        self.assertEqual(machine_slots.count(), 1)

        for machine_slot in machine_slots:
            self.assertEqual(machine_slot.machine_id, 1)

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
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        # Test exact overlap with a second opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')

        # Test opening start before, and end during an existing opening
        response = self.create_opening_slot(start_time='09:00', end_time='11:00',)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')
        self.assertEqual(response.context_data['form'].data['start_time'], datetime.time(9))
        self.assertEqual(response.context_data['form'].data['end_time'], datetime.time(10))

        # Test opening start during an existing opening, and end after
        response = self.create_opening_slot(start_time='11:00', end_time='13:00',)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')
        self.assertEqual(response.context_data['form'].data['start_time'], datetime.time(12))
        self.assertEqual(response.context_data['form'].data['end_time'], datetime.time(13))

    def test_view_valid(self):
        response = self.create_opening_slot()
        
        obj = OpeningSlot.objects.latest('id')
        self.assertEqual(obj.start, datetime.datetime(2023, 5, 1, 10, 0))
        self.assertEqual(obj.end, datetime.datetime(2023, 5, 1, 12, 0))
        self.assertEqual(obj.comment, 'my comment')
        self.assertEqual(obj.user, self.superuser)
        self.assertEqual(obj.get_machine_list, [self.trotec])
        self.assertEqual(obj.opening, self.openlab)

    def test_get_success_message(self):
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        storage = get_messages(response.wsgi_request)
        messages = [message.message for message in storage]

        expected_message = """
            Votre ouverture a été créée avec succès le 
            lundi 1 mai 2023 de 10:00 à 12:00
            </br>
            <a href="/fabcal/download-ics-file/OpenLab/2023-05-01 10:00:00/2023-05-01 12:00:00">
            <i class="bi bi-file-earmark-arrow-down-fill"> </i> Ajouter à mon calendrier</a>
        """
        expected_message = re.sub(r'\s{2,}', ' ', expected_message.replace('\n', '')).strip()

        self.assertEqual(messages, [expected_message])

    def test_success_url(self):
        """
        Test the success url.
        """
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)
        self.assertIn('/schedule', response.url)
    
    def tearDown(self):
        self.client.logout()
        self.superuser.delete()
        self.group.delete()

class OpeningSlotUpdateViewTestCase(SlotViewTestCase):
    def setUp(self):
        super().setUp()
        self.update_url = reverse('fabcal:openingslot-update', kwargs={'pk': 1})

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(OpeningSlotUpdateView, SuperuserRequiredMixin))

    def test_get_initial_and_messages(self):
        OpeningSlot.objects.all().delete()

        # Create a first opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        # test initial value befor uptdating the opening slot
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial

        self.assertEqual(form_data['comment'], 'my comment')
        self.assertEqual(form_data['opening'], 1)
        self.assertEqual(form_data['date'], '2023-05-01')
        self.assertEqual(form_data['start_time'], '10:00')
        self.assertEqual(form_data['end_time'], '12:00')
        self.assertEqual(form_data['machines'], [1])

        # test message after confirm updating the opening slot
        self.client.login(username='testsuperuser', password='testpass')
        response = self.client.post(self.update_url, form_data)
        storage = get_messages(response.wsgi_request)
        messages = [message.message for message in storage]

        expected_message = """
            Votre ouverture a été mise à jour avec succès le 
            lundi 1 mai 2023 de 10:00 à 12:00
            </br>
            <a href="/fabcal/download-ics-file/OpenLab/2023-05-01 10:00:00/2023-05-01 12:00:00">
            <i class="bi bi-file-earmark-arrow-down-fill"> </i> Ajouter à mon calendrier</a>
        """
        expected_message = re.sub(r'\s{2,}', ' ', expected_message.replace('\n', '')).strip()

        self.assertEqual(messages, [expected_message])

    def test_overlap(self):
        OpeningSlot.objects.all().delete()
        self.client.login(username='testsuperuser', password='testpass')
        
        # Create a first opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        # Create a seconde opening after
        response = self.create_opening_slot(start_time='13:00', end_time='14:00')
        self.assertEqual(response.status_code, 302)

        # Create a seconde opening before
        response = self.create_opening_slot(start_time='08:00', end_time='09:00')
        self.assertEqual(response.status_code, 302)

        # Extend first opening with valid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['end_time'] = '13:00' # instead of 12:00

        response = self.client.post(self.update_url, form_data)
        self.assertEqual(response.status_code, 200)

        # Extend first opening with invalid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['end_time'] = '14:00' # instead of 13:00

        response = self.client.post(self.update_url, form_data)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')
        self.assertEqual(response.context_data['form'].data['start_time'], datetime.time(10))
        self.assertEqual(response.context_data['form'].data['end_time'], datetime.time(13))

        # Extend first opening with invalid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '08:30' # instead of 09:00

        response = self.client.post(self.update_url, form_data)
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_openings')
        self.assertEqual(response.context_data['form'].data['start_time'], datetime.time(9))
        self.assertEqual(response.context_data['form'].data['end_time'], datetime.time(12))

    def test_opening_slot_extend(self):
        OpeningSlot.objects.all().delete()
        self.client.login(username='testsuperuser', password='testpass')
        
        # Create a opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        # Extend opening with valid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '9:00' # instead of 10:00
        form_data['end_time'] = '13:00' # instead of 12:00

        response = self.client.post(self.update_url, form_data)
        self.assertEqual(response.status_code, 302)

        # Assert machine slot extend if no reservation
        machine_slot = MachineSlot.objects.first()
        self.assertEqual(MachineSlot.objects.first().start, datetime.datetime(2023, 5, 1, 9, 0))
        self.assertEqual(MachineSlot.objects.first().end, datetime.datetime(2023, 5, 1, 13, 0))

        # Add reservation
        machine_slot.user = self.user
        machine_slot.save()

        # Extend opening with valid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '8:00' # instead of 9:00
        form_data['end_time'] = '14:00' # instead of 13:00

        response = self.client.post(self.update_url, form_data)
        self.assertEqual(response.status_code, 302)

        # Assert machine slot extend if reservation
        qs = MachineSlot.objects.all().order_by('start')
        self.assertEqual(qs.all().count(), 3)

        self.assertEqual(qs.first().start, datetime.datetime(2023, 5, 1, 8, 0))        
        self.assertEqual(qs.first().end, datetime.datetime(2023, 5, 1, 9, 0))
        self.assertEqual(qs.first().user, None)

        self.assertEqual(qs.last().start, datetime.datetime(2023, 5, 1, 13, 0))
        self.assertEqual(qs.last().end, datetime.datetime(2023, 5, 1, 14, 0))
        self.assertEqual(qs.last().user, None)

    def test_opening_slot_shorten(self):
        OpeningSlot.objects.all().delete()
        self.client.login(username='testsuperuser', password='testpass')
        
        # Create a opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        # Shorten opening with valid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '10:30' # instead of 10:00
        form_data['end_time'] = '11:30' # instead of 12:00

        response = self.client.post(self.update_url, form_data)
        self.assertEqual(response.status_code, 302)

        # Assert machine slot shorten if no reservation
        machine_slot = MachineSlot.objects.first()
        self.assertEqual(MachineSlot.objects.first().start, datetime.datetime(2023, 5, 1, 10, 30))
        self.assertEqual(MachineSlot.objects.first().end, datetime.datetime(2023, 5, 1, 11, 30))

        # Add reservation
        machine_slot.user = self.user
        machine_slot.save()

        # Shorter opening with valid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '11:00' # instead of 9:00
        form_data['end_time'] = '11:30' # instead of 13:00

        response = self.client.post(self.update_url, form_data)

        # Assert machine slot shorten if reservation
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_reservation')
        self.assertEqual(response.context_data['form'].data['start_time'], datetime.time(10, 30))
        self.assertEqual(response.context_data['form'].data['end_time'], datetime.time(11, 30))

        # Shorter opening with valid time
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '10:30' # instead of 9:00
        form_data['end_time'] = '11:00' # instead of 13:00

        response = self.client.post(self.update_url, form_data)

        # Assert machine slot shorten if reservation
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'conflicting_reservation')
        self.assertEqual(response.context_data['form'].data['start_time'], datetime.time(10, 30))
        self.assertEqual(response.context_data['form'].data['end_time'], datetime.time(11, 30))

    def test_add_remove_machine(self):
        OpeningSlot.objects.all().delete()
        self.client.login(username='testsuperuser', password='testpass')
        
        # Create a opening
        response = self.create_opening_slot()

        # Assert only 1 Trotec machine slot
        self.assertEqual(MachineSlot.objects.all().count(), 1)
        self.assertEqual(MachineSlot.objects.first().machine.title, 'Trotec')

        # Add a new machine to the opening
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['machines'].append(Machine.objects.get(title = 'Prusa').pk)

        response = self.client.post(self.update_url, form_data)

        # Assert 2 machine slots
        self.assertEqual(MachineSlot.objects.all().count(), 2)
        self.assertEqual(MachineSlot.objects.first().machine.title, 'Trotec')
        self.assertEqual(MachineSlot.objects.last().machine.title, 'Prusa')
        self.assertEqual(MachineSlot.objects.last().opening_slot, OpeningSlot.objects.first())

        # Add reservation to Trotec
        machine_slot = MachineSlot.objects.first()
        machine_slot.user = self.user
        machine_slot.save()

        # Try to delete machine Trotec
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['machines'].remove(Machine.objects.get(title = 'Trotec').pk)
        response = self.client.post(self.update_url, form_data)

        # Assert unable to delete because of the reservation
        self.assertEqual(response.context_data['form'].errors.as_data()['__all__'][0].code, 'machine_slot_has_reservation')
        self.assertEqual(MachineSlot.objects.all().count(), 2)

        # Try to delete machine Prusa
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['machines'].remove(Machine.objects.get(title = 'Prusa').pk)
        response = self.client.post(self.update_url, form_data)

        # Assert Prusa machine slot removed
        self.assertEqual(MachineSlot.objects.all().count(), 1)
        self.assertEqual(response.status_code, 302)

    def test_success_url(self):
        """
        Test the success url.
        """
        response = self.create_opening_slot()

        # Update opening
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['machines'].append(Machine.objects.get(title = 'Prusa').pk)

        response = self.client.post(self.update_url, form_data)
        self.assertRedirects(response, reverse('accounts:profile'))

class OpeningSlotDeleteViewTestCase(SlotViewTestCase):
    def setUp(self):
        super().setUp()
        self.delete_url = reverse('fabcal:openingslot-delete', kwargs={'pk': 1})

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(OpeningSlotDeleteView, SuperuserRequiredMixin))

    def test_delete_opening_slot(self):
        OpeningSlot.objects.all().delete()
        self.client.login(username='testsuperuser', password='testpass')
        
        # Create a opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        # Add reservation
        machine_slot = MachineSlot.objects.first()
        machine_slot.user = self.user
        machine_slot.save()

        # Try to delete reservation
        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Tu ne peux pas supprimer cette ouverture car il y a des réservations'
        self.assertEqual(message, expected_message)
        self.assertEqual(OpeningSlot.objects.all().count(), 1)
        self.assertEqual(MachineSlot.objects.all().count(), 1)

        # Remove reservation
        machine_slot.user = None
        machine_slot.save()

        # Delete reservation
        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre ouverture du lundi 1 mai 2023 de 10:00 à 12:00 a bien été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(OpeningSlot.objects.all().count(), 0)
        self.assertEqual(MachineSlot.objects.all().count(), 0)

class MachineSlotUpdateViewTestCase(SlotViewTestCase):
    def setUp(self):
        super().setUp()
        self.update_url = reverse('fabcal:machineslot-update', kwargs={'pk': 1})

        OpeningSlot.objects.all().delete()
        self.client.login(username='user', password='userpassword')
        
        # Create a opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

    def test_LoginRequiredMixin(self):
        self.assertTrue(issubclass(MachineSlotUpdateView, LoginRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_machine_slot_middle_form(self, mock_send_mail):
        """
        This test tests if a slot is created in the middle of the slot
        """

        # Add reservation
        form_data = {
            'start_time': '10:30',
            'end_time': '11:30'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertTrue(form.is_valid())

        machine_slot = form.save()
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        
        self.assertEqual(call_args.kwargs['recipient_list'], ['user@fake.django'])
        self.assertEqual(call_args.kwargs['subject'], 'Confirmation de votre réservation machine')

        self.assertEqual(machine_slot.user, self.user)
        self.assertEqual(MachineSlot.objects.all().count(), 3)

        machine_slot_prev = MachineSlot.objects.get(pk=2)
        self.assertEqual(machine_slot_prev.user, None)
        self.assertEqual(machine_slot_prev.start.time(), datetime.time(10))
        self.assertEqual(machine_slot_prev.end.time(), datetime.time(10,30))

        machine_slot_next = MachineSlot.objects.get(pk=3)
        self.assertEqual(machine_slot_next.user, None)
        self.assertEqual(machine_slot_next.start.time(), datetime.time(11,30))
        self.assertEqual(machine_slot_next.end.time(), datetime.time(12))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_machine_slot_start_form(self, mock_send_mail):
        """
        This test tests if a slot is created in the start of the slot
        """

        # Add reservation
        form_data = {
            'start_time': '10:00',
            'end_time': '11:30'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertTrue(form.is_valid())

        machine_slot = form.save()
        self.assertEqual(machine_slot.user, self.user)
        self.assertEqual(MachineSlot.objects.all().count(), 2)

        machine_slot_next = MachineSlot.objects.get(pk=2)
        self.assertEqual(machine_slot_next.user, None)
        self.assertEqual(machine_slot_next.start.time(), datetime.time(11,30))
        self.assertEqual(machine_slot_next.end.time(), datetime.time(12))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_machine_slot_end_form(self, mock_send_mail):
        """
        This test tests if a slot is created in the end of the slot
        """

        # Add reservation
        form_data = {
            'start_time': '10:30',
            'end_time': '12:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertTrue(form.is_valid())

        machine_slot = form.save()
        self.assertEqual(machine_slot.user, self.user)
        self.assertEqual(MachineSlot.objects.all().count(), 2)

        machine_slot_prev = MachineSlot.objects.get(pk=2)
        self.assertEqual(machine_slot_prev.user, None)
        self.assertEqual(machine_slot_prev.start.time(), datetime.time(10,00))
        self.assertEqual(machine_slot_prev.end.time(), datetime.time(10,30))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_machine_slot_starting_with_whole_slot(self, mock_send_mail):
        """
        This test tests if a slot is created in the whole slot, and then modified. 
        This check the next_slot is not None
        """
        # Add reservation
        form_data = {
            'start_time': '10:00',
            'end_time': '12:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()

        # Update reservation, modify the end time
        form_data['end_time'] = '11:30'
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()

        self.assertEqual(MachineSlot.objects.all().count(), 2)
        self.assertEqual(machine_slot.user, self.user)
        self.assertEqual(MachineSlot.objects.last().start.time(), datetime.time(11,30))
        self.assertEqual(MachineSlot.objects.last().end.time(), datetime.time(12,00))
        self.assertEqual(MachineSlot.objects.last().user, None)

        # Update reservation, modify the start time 
        form_data['start_time'] = '10:30'
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()

        self.assertEqual(MachineSlot.objects.all().count(), 3)
        self.assertEqual(machine_slot.user, self.user)
        self.assertEqual(MachineSlot.objects.last().start.time(), datetime.time(10,00))
        self.assertEqual(MachineSlot.objects.last().end.time(), datetime.time(10,30))
        self.assertEqual(MachineSlot.objects.last().user, None)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_extend_machine_slot_form(self, mock_send_mail):
        """
        This test tests if a slot is extended
        """

        instance = MachineSlot.objects.first()

        # Add reservation
        form_data = {
            'start_time': '10:30',
            'end_time': '11:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=instance, user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()
        self.assertEqual(MachineSlot.objects.all().count(), 3)

        # slice reservation for 30 minutes
        form_data = {
            'start_time': '11:00',
            'end_time': '11:30'
        }

        form_initial = {
            'start_time': instance.start.time(),
            'end_time': instance.end.time()
        }

        form = MachineSlotUpdateForm(data=form_data, instance=instance, initial=form_initial, user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()

        self.assertEqual(MachineSlot.objects.all().count(), 3)

        self.assertEqual(instance.start.time(), datetime.time(11,00))
        self.assertEqual(instance.end.time(), datetime.time(11,30))

        previous_machine_slots = instance.previous_slots(instance.start-datetime.timedelta(days=1))
        self.assertEqual(previous_machine_slots.count(), 1)
        self.assertEqual(previous_machine_slots.first().start.time(), datetime.time(10))
        self.assertEqual(previous_machine_slots.first().end.time(), datetime.time(11))

        next_machine_slots = instance.next_slots(instance.start+datetime.timedelta(days=1))
        self.assertEqual(next_machine_slots.count(), 1)
        self.assertEqual(next_machine_slots.first().start.time(), datetime.time(11, 30))
        self.assertEqual(next_machine_slots.first().end.time(), datetime.time(12, 00))

        # extend reservation for -1h minutes
        form_data = {
            'start_time': '10:00',
            'end_time': '11:30'
        }

        form_initial = {
            'start_time': instance.start.time(),
            'end_time': instance.end.time()
        }

        form = MachineSlotUpdateForm(data=form_data, instance=instance, initial=form_initial, user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()

        self.assertEqual(MachineSlot.objects.all().count(), 2)

        self.assertEqual(instance.start.time(), datetime.time(10,00))
        self.assertEqual(instance.end.time(), datetime.time(11,30))

        previous_machine_slots = instance.previous_slots(instance.start-datetime.timedelta(days=1))
        self.assertEqual(previous_machine_slots.count(), 0)

        next_machine_slots = instance.next_slots(instance.start+datetime.timedelta(days=1))
        self.assertEqual(next_machine_slots.count(), 1)
        self.assertEqual(next_machine_slots.first().start.time(), datetime.time(11, 30))
        self.assertEqual(next_machine_slots.first().end.time(), datetime.time(12, 00))

        # extend reservation for +30 minutes
        form_data = {
            'start_time': '10:00',
            'end_time': '12:00'
        }

        # to be tested if remove _time and .time()
        form_initial = {
            'start': instance.start,
            'end': instance.end
        }

        form = MachineSlotUpdateForm(data=form_data, instance=instance, initial=form_initial, user=self.user)
        self.assertTrue(form.is_valid())
        machine_slot = form.save()

        self.assertEqual(MachineSlot.objects.all().count(), 1)

        self.assertEqual(instance.start.time(), datetime.time(10,00))
        self.assertEqual(instance.end.time(), datetime.time(12,00))

    def test_update_machine_slot_invalid_start_time(self):
        """
        Test if the user input start time is before the slot range.
        """

        # Test reservation start before machine slot
        form_data = {
            'start_time': '08:30',
            'end_time': '11:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['start_time'][0].code, 'invalid_start_time')
        self.assertEqual(form.errors.as_data()['start_time'][0].message, 'Vous ne pouvez pas commencer avant %(start_time)s')

    def test_update_machine_slot_invalid_end_time(self):
        """
        Test if the user input end time is after the slot range.
        """

        # Test reservation after before machine slot
        form_data = {
            'start_time': '10:30',
            'end_time': '14:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['end_time'][0].code, 'invalid_end_time')
        self.assertEqual(form.errors.as_data()['end_time'][0].message, 'Vous ne pouvez pas finir après %(end_time)s')

    def test_update_machine_slot_invalid_minimum_duration(self):
        """
        Test if the user input reservation duration is less than 30 minutes.
        """

        # Test reservation less than 30 min
        form_data = {
            'start_time': '10:30',
            'end_time': '10:45'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['__all__'][0].code, 'invalid_minimum_duration')
        self.assertEqual(form.errors.as_data()['__all__'][0].message, 'Veuillez réserver minimum %(time)s minutes')

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_slots_availability(self, mock_send_mail):
        """
        Test the slots availability by creating valid and invalid machine slots with different users and checking for errors.
        """

        # create valid machine slot with user A
        form_data = {
            'start_time': '10:00',
            'end_time': '10:30'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.last(), user=self.superuser)
        form.is_valid()
        form.save()
        self.assertEqual(MachineSlot.objects.all().count(), 2)

        # create valid machine slot with user A
        form_data = {
            'start_time': '11:30',
            'end_time': '12:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.last(), user=self.superuser)
        form.is_valid()
        form.save()
        self.assertEqual(MachineSlot.objects.all().count(), 3)

        # create valid machine slot with user B
        form_data = {
            'start_time': '10:30',
            'end_time': '11:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.last(), user=self.user)
        form.is_valid()
        machine_slot = form.save()
        self.assertEqual(MachineSlot.objects.all().count(), 4)

        # setup invalid datetime
        form_initial = {
            'start': form.cleaned_data['start'],
            'end': form.cleaned_data['end']
        }

        # Update with invalid datetime, machine slot booked sooner
        form_data = {
            'start_time': '10:30',
            'end_time': '12:00'
        }
        
        form = MachineSlotUpdateForm(data=form_data, instance=machine_slot, initial=form_initial, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['__all__'][0].message, 'La machine est déjà réservée depuis %(time)s')
        self.assertEqual(form.errors.as_data()['__all__'][0].code, 'machine_slot_already_booked')

        # Update with invalid datetime, machine slot booked sooner
        form_data = {
            'start_time': '10:00',
            'end_time': '11:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.last(), initial=form_initial, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['__all__'][0].message, "La machine est déjà réservée jusqu'à %(time)s")
        self.assertEqual(form.errors.as_data()['__all__'][0].code, 'machine_slot_already_booked')

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_machine_slot_invalid_duration(self, mock_send_mail):
        """
        Test if the user input reservation duration is not a multiple of 30 minutes.
        """

        # Test reservation of 45 min (not multiple of 30 min)
        form_data = {
            'start_time': '10:30',
            'end_time': '11:15'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors.as_data()['__all__'][0].code, 'invalid_duration')
        self.assertEqual(form.errors.as_data()['__all__'][0].message, 'Veuillez réserver des tranches de %(time)s minutes')

    def test_dispatch_redirect_if_not_trained(self):
        """
        Dispatches redirect if the user is not trained.
        """
        response = self.client.get(self.update_url)
        self.assertTrue(response.url, '/trainings/?machine_category=1')
    
    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_machine_slot_success_message(self, mock_send_mail):
        """
        Test the successful update of a machine slot and the resulting message.
        """

        TrainingValidation.objects.create(
            profile=self.user.profile,
            training=self.laser_training
        )

        self.client.login(username='user', password='userpassword')
        # Test update machine slot message
        response = self.client.get(self.update_url)
        form_data = response.context_data['form'].initial
        form_data['start_time'] = '10:30'
        form_data['end_time'] = '11:00'

        response = self.client.post(self.update_url, form_data)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = "Vous avez réservé avec succès la machine Trotec durant 30 minutes le lundi 1 mai 2023 de 10:30 à 11:00"
        self.assertEqual(message, expected_message)

    def test_create_email_content(self):
        """
        Test the creation of email content for a reservation, including validation and assertions.
        """

        # Test reservation of 45 min (not multiple of 30 min)
        form_data = {
            'start_time': '10:30',
            'end_time': '11:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)
        self.assertTrue(form.is_valid())

        email_content = form.create_email_content()
        self.assertEqual(email_content['recipient_list'], ['user@fake.django'])
        self.assertEqual(email_content['subject'], 'Confirmation de votre réservation machine')

class MachineSlotDeleteViewTestCase(SlotViewTestCase):
    """
    Test the deletion of a machine slot.
    """

    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super().setUp()
        self.update_url = reverse('fabcal:machineslot-update', kwargs={'pk': 1})
        self.delete_url = reverse('fabcal:machineslot-delete', kwargs={'pk': 1})

        OpeningSlot.objects.all().delete()
        
        # Create a opening
        response = self.create_opening_slot()
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user', password='userpassword')

        # Create a machine slot
        form_data = {
            'start_time': '10:30',
            'end_time': '11:30'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.first(), user=self.user)
        form.is_valid()
        form.save()

    def test_dispatch_permission(self):
        """
        Function to test dispatch permission. 
        """
        self.client.login(username='testsuperuser', password='testpass')

        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_LoginRequiredMixin(self):
        """
        Test case for the LoginRequiredMixin function.
        """
        self.assertTrue(issubclass(MachineSlotDeleteView, LoginRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_delete_machine_slot(self, mock_send_mail):
        """
        Test the deletion of a machine slot.
        """

        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre réservation a été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MachineSlot.objects.count(), 1)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_delete_machine_slot_with_slots_booked_after(self, mock_send_mail):
        """
        Test for deleting a machine slot with slots booked after.
        """

        # Create a machine slot another
        form_data = {
            'start_time': '11:30',
            'end_time': '12:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.last(), user=self.user)
        form.is_valid()
        form.save()

        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre réservation a été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MachineSlot.objects.count(), 2)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_delete_machine_slot_with_slots_booked_before(self, mock_send_mail):
        """
        Test for deleting a machine slot with slots booked before.
        """

        # Create a machine slot another
        form_data = {
            'start_time': '10:00',
            'end_time': '10:30'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.get(pk=2), user=self.user)
        form.is_valid()
        form.save()

        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre réservation a été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MachineSlot.objects.count(), 2)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_delete_machine_slot_with_slots_booked_before_and_after(self, mock_send_mail):
        """
        Test for deleting a machine slot with slots booked before and after.
        """

        # Create a machine slot another
        form_data = {
            'start_time': '11:30',
            'end_time': '12:00'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.last(), user=self.user)
        form.is_valid()
        form.save()

        # Create a machine slot another
        form_data = {
            'start_time': '10:00',
            'end_time': '10:30'
        }
        form = MachineSlotUpdateForm(data=form_data, instance=MachineSlot.objects.get(pk=2), user=self.user)
        form.is_valid()
        form.save()

        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre réservation a été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MachineSlot.objects.count(), 3)

class TrainingSlotTestCase(SlotViewTestCase):
    def setUp(self):
        super().setUp()

        self.form_data = self.get_default_form_data()
        self.form_data['training'] = Training.objects.first().pk
        self.form_data['registration_limit'] = 1

        # add user for notification
        TrainingNotification.objects.create(
            profile=self.user.profile,
            training=self.laser_training
        )

class TrainingSlotCreateViewTestCase(TrainingSlotTestCase):

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(TrainingSlotCreateView, SuperuserRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_create_training_slot_form(self, mock_send_mail):
        """
        Test the creation of a training slot form and its associated functionality.
        """

        form = TrainingSlotCreateForm(data=self.form_data, user=self.user)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(TrainingSlot.objects.count(), 1)
        self.assertEqual(TrainingSlot.objects.first().start, datetime.datetime(2023, 5, 1, 10))
        self.assertEqual(TrainingSlot.objects.first().end, datetime.datetime(2023, 5, 1, 12))
        self.assertEqual(TrainingSlot.objects.first().user, self.user)
        self.assertEqual(TrainingSlot.objects.first().opening_slot, OpeningSlot.objects.first())
        
        self.assertEqual(OpeningSlot.objects.count(), 1)
        self.assertEqual(OpeningSlot.objects.first().start, datetime.datetime(2023, 5, 1, 10))
        self.assertEqual(OpeningSlot.objects.first().end, datetime.datetime(2023, 5, 1, 12))

        email_content = form.create_email_content()
        self.assertEqual(email_content['recipient_list'], ['user@fake.django'])
        self.assertEqual(email_content['subject'], 'Une nouvelle formation a été planifiée')

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_success_message(self, mock_send_mail):
        """
        Test the success message returned by the get_success_message function.
        """
        create_url = reverse('fabcal:trainingslot-create', kwargs=self.get_creation_url_parameter())

        self.client.login(username='testsuperuser', password='testpass')

        response = self.client.post(create_url, self.form_data)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Vous avez créé avec succès la formation laser durant 120 minutes le lundi 1 mai 2023 de 10:00 à 12:00'
        self.assertEqual(message, expected_message)

class TrainingSlotUpdateViewTestCase(TrainingSlotTestCase):

    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super().setUp()

        form = TrainingSlotCreateForm(data=self.form_data, user=self.user)
        self.assertTrue(form.is_valid())
        training_slot = form.save()

        self.form_initial = {
            'start': training_slot.start,
            'end': training_slot.end
        }

        # setup new start and end time
        self.form_data['start_time'] = '11:30'
        self.form_data['end_time'] = '13:00'

        self.update_url = reverse('fabcal:trainingslot-update', kwargs={'pk': 1})

    def test_SuperuserRequiredMixin(self):
        """
        Test case for the SuperuserRequiredMixin function.
        """
        self.assertTrue(issubclass(TrainingSlotCreateView, SuperuserRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_update_training_slot_form(self, mock_send_mail):
        """
        Test the update_training_slot_form function
        """

        instance = TrainingSlot.objects.first()

        form = TrainingSlotUpdateForm(
            data=self.form_data,
            instance=TrainingSlot.objects.first(),
            user=self.user,
            initial=self.form_initial,
        )

        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(TrainingSlot.objects.count(), 1)
        self.assertEqual(TrainingSlot.objects.first().start, datetime.datetime(2023, 5, 1, 11, 30))
        self.assertEqual(TrainingSlot.objects.first().end, datetime.datetime(2023, 5, 1, 13))

        self.assertEqual(OpeningSlot.objects.count(), 1)
        self.assertEqual(OpeningSlot.objects.first().start, datetime.datetime(2023, 5, 1, 11, 30))
        self.assertEqual(OpeningSlot.objects.first().end, datetime.datetime(2023, 5, 1, 13))

        email_content = form.create_email_content()
        self.assertEqual(email_content['recipient_list'], ['user@fake.django'])
        self.assertEqual(email_content['subject'], 'Une formation a été mise à jour')

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_success_message(self, mock_send_mail):
        create_url = reverse('fabcal:trainingslot-update', kwargs={'pk': 1})

        self.client.login(username='testsuperuser', password='testpass')

        response = self.client.post(create_url, self.form_data)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Vous avez créé avec succès la formation laser durant 90 minutes le lundi 1 mai 2023 de 11:30 à 13:00'
        self.assertEqual(message, expected_message)

class TrainingSlotDeleteViewTestCase(TrainingSlotTestCase):

    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super().setUp()

        form = TrainingSlotCreateForm(data=self.form_data, user=self.superuser)
        self.assertTrue(form.is_valid())
        self.training_slot = form.save()
        self.delete_url = reverse('fabcal:trainingslot-delete', kwargs={'pk': 1})

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(TrainingSlotDeleteView, SuperuserRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_delete_training_slot(self, mock_send_mail):
        # add registration
        form=TrainingSlotRegistrationCreateForm(instance=self.training_slot, user=self.user)
        form.save()

        self.client.login(username='testsuperuser', password='testpass')
        
        # test invalid deletion due to registration
        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        self.assertEqual(self.client.session.get('error_code', None), "training_slot_with_registrations")

        # remove registration
        form=TrainingSlotRegistrationDeleteForm(instance=self.training_slot, user=self.user)
        form.save()

        self.assertEqual(self.training_slot.registrations.first(), None)

        # Delete slot
        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre formation du lundi 1 mai 2023 de 10:00 à 12:00 a bien été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(TrainingSlot.objects.all().count(), 0)

class TrainingSlotRegistrationViewTestCase(TrainingSlotTestCase):

    def setUp(self, ):
        super().setUp()

        form = TrainingSlotCreateForm(data=self.form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.training_slot = form.save()

class TrainingSlotRegistrationCreateViewTestCase(TrainingSlotRegistrationViewTestCase):
    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super(TrainingSlotRegistrationCreateViewTestCase, self).setUp()
        self.create_url = reverse('fabcal:trainingslot-register', kwargs={'pk': self.training_slot.pk})
    
    def test_LoginRequiredMixin(self):
        self.assertTrue(issubclass(TrainingSlotRegistrationCreateView, LoginRequiredMixin))
    @patch('fabcal.forms.send_mail', autospec=True)
    def test_training_slot_registration_create_form(self, mock_send_mail):

        form=TrainingSlotRegistrationCreateForm(instance=self.training_slot, user=self.user)
        training_slot = form.save()

        email_content = form.create_email_content()
        self.assertEqual(training_slot.registrations.first(), self.user)
        self.assertEqual(email_content['recipient_list'], [self.user.email])
        self.assertEqual(email_content['subject'], "Confirmation de l'inscrition à la formation")

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_success_message(self, mock_send_mail):
        """
        Test the get_success_message function by checking if the correct message is displayed after registering for a training session.
        """
        
        self.client.login(username='user', password='userpassword')
        response = self.client.post(self.create_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Vous vous êtes inscrit avec succès à la formation laser pendant 120 minutes le lundi 1 mai 2023 de 10:00 à 12:00'
        self.assertEqual(message, expected_message)
    
    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_dispatch_message_when_already_registered(self, mock_send_mail):
        self.client.login(username='user', password='userpassword')
        response = self.client.post(self.create_url)
        response = self.client.post(self.create_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = "Vous êtes déjà inscrit à cette formation !"
        self.assertEqual(message, expected_message)

class TrainingSlotRegistrationDeleteViewTestCase(TrainingSlotRegistrationViewTestCase):

    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super(TrainingSlotRegistrationDeleteViewTestCase, self).setUp()

        form=TrainingSlotRegistrationCreateForm(instance=self.training_slot, user=self.user)
        self.training_slot = form.save()

        self.delete_url = reverse('fabcal:trainingslot-unregister', kwargs={'pk': 1})

    def test_LoginRequiredMixin(self):
        self.assertTrue(issubclass(TrainingSlotRegistrationDeleteView, LoginRequiredMixin))
    @patch('fabcal.forms.send_mail', autospec=True)
    def test_training_slot_registration_delete_form(self, mock_send_mail):
        """
        Test the training slot registration delete form.
        """

        form=TrainingSlotRegistrationDeleteForm(instance=self.training_slot, user=self.user)
        form.save()

        email_content = form.create_email_content()
        self.assertEqual(self.training_slot.registrations.first(), None)
        self.assertEqual(email_content['recipient_list'], [self.user.email])
        self.assertEqual(email_content['subject'], 'Training unregistration confirmation')

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_dispatch_user_in_registrations(self, mock_send_mail):
        """
        Test case for when the user is in registrations.
        """

        self.client.login(username='user', password='userpassword')
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_dispatch_user_not_in_registrations(self, mock_send_mail):
        """
        Test case for when the user is not in registrations.
        """
        
        self.client.login(username='testsuperuser', password='testpass')
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_success_message(self, mock_send_mail):
        """
        Test the get_success_message function with a mocked send_mail function.
        """

        self.client.login(username='user', password='userpassword')

        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Vous avez créé avec succès la formation laser durant 120 minutes le lundi 1 mai 2023 de 10:00 à 12:00'
        self.assertEqual(message, expected_message)

class EventSlotTestCase(SlotViewTestCase):
    def setUp(self):
        super().setUp()

        self.form_data = self.get_default_form_data()
        self.form_data = self.get_default_form_data()
        self.form_data['event'] = Event.objects.first().pk
        self.form_data['price'] = '10 CHF'
        self.form_data['has_registration'] = True
        self.form_data['registration_limit'] = 10

class EventSlotCreateViewTestCase(EventSlotTestCase):

    def test_superuser_required(self):
        self.assertTrue(issubclass(EventSlotCreateView, SuperuserRequiredMixin))

    def test_event_slot_create_form_without_opening(self):
        """
        Test the event slot create form.
        """
        self.form_data['opening'] = None
        form=EventSlotCreateForm(data=self.form_data, user=self.superuser)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(EventSlot.objects.count(), 1)
        self.assertEqual(OpeningSlot.objects.count(), 0)
        self.assertEqual(EventSlot.objects.first().start, datetime.datetime(2023, 5, 1, 10))
        self.assertEqual(EventSlot.objects.first().end, datetime.datetime(2023, 5, 1, 12))
        self.assertEqual(EventSlot.objects.first().user, self.superuser)

    def test_event_slot_create_form_with_opening(self):
        """
        Test the event slot create form and an opening.
        """

        self.form_data['opening'] = Opening.objects.first().pk

        form=EventSlotCreateForm(data=self.form_data, user=self.superuser)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(EventSlot.objects.count(), 1)
        self.assertEqual(OpeningSlot.objects.count(), 1)
    
    def test_get_success_message(self):
        """
        Test the success message returned by the get_success_message function.
        """
        create_url = reverse('fabcal:eventslot-create', kwargs=self.get_creation_url_parameter())

        self.client.login(username='testsuperuser', password='testpass')

        response = self.client.post(create_url, self.form_data)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = "Vous avez créé avec succès l'évènement my event title durant 120 minutes le lundi 1 mai 2023 de 10:00 à 12:00"
        self.assertEqual(message, expected_message)
    
    def test_success_url(self):
        """
        Test the success url.
        """
        create_url = reverse('fabcal:eventslot-create', kwargs=self.get_creation_url_parameter())

        self.client.login(username='testsuperuser', password='testpass')

        response = self.client.post(create_url, self.form_data)
        self.assertRedirects(response, reverse('fabcal:eventslot-detail', kwargs={'pk': EventSlot.objects.first().pk}))

class EventSlotUpdateViewTestCase(EventSlotTestCase):
    def setUp(self):
        super().setUp()

        form=EventSlotCreateForm(data=self.form_data, user=self.superuser)
        form.is_valid()
        event_slot = form.save()

        self.form_initial = {
            'start': event_slot.start,
            'end': event_slot.end
        }
    
    def test_superuser_required(self):
        self.assertTrue(issubclass(EventSlotUpdateView, SuperuserRequiredMixin))

    def test_event_slot_update_form(self):
        """
        Test the event slot update form.
        """

        self.form_data['start_time'] = '10:30'
        self.form_data['price'] = '5 CHF'
        self.form_data['opening'] = Opening.objects.first().pk
        self.form_data['machine'] = [Machine.objects.first().pk]


        form=EventSlotUpdateForm(data=self.form_data, instance=EventSlot.objects.first(), user=self.superuser, initial=self.form_initial)
        self.assertTrue(form.is_valid())
        form.save()

        self.assertEqual(EventSlot.objects.count(), 1)
        self.assertEqual(EventSlot.objects.first().price, '5 CHF')
        self.assertEqual(EventSlot.objects.first().start, datetime.datetime(2023, 5, 1, 10, 30))
        self.assertEqual(EventSlot.objects.first().opening_slot, OpeningSlot.objects.first())

    def test_get_success_message(self):
        """
        Test the success message returned by the get_success_message function.
        """
        update_url = reverse('fabcal:eventslot-update', kwargs={'pk': 1})

        self.client.login(username='testsuperuser', password='testpass')

        self.form_data['start_time'] = '10:30'
        response = self.client.post(update_url, self.form_data)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = "Vous avez mis à jour avec succès l'évènement my event title durant 90 minutes le lundi 1 mai 2023 de 10:30 à 12:00"
        self.assertEqual(message, expected_message)

    def test_success_url(self):
        """
        Test the success url.
        """
        update_url = reverse('fabcal:eventslot-update', kwargs={'pk': 1})

        self.client.login(username='testsuperuser', password='testpass')

        response = self.client.post(update_url, self.form_data)
        self.assertRedirects(response, reverse('fabcal:eventslot-detail', kwargs={'pk': EventSlot.objects.first().pk}))

class EventSlotDeleteViewTestCase(EventSlotTestCase):

    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super().setUp()

        form = EventSlotCreateForm(data=self.form_data, user=self.superuser)
        self.assertTrue(form.is_valid())
        self.event_slot = form.save()
        self.delete_url = reverse('fabcal:eventslot-delete', kwargs={'pk': 1})

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(EventSlotDeleteView, SuperuserRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_delete_event_slot(self, mock_send_mail):
        # add registration
        form=EventSlotRegistrationCreateForm(instance=self.event_slot, user=self.user)
        form.save()

        self.client.login(username='testsuperuser', password='testpass')
        
        # test invalid deletion due to registration
        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        self.assertEqual(self.client.session.get('error_code', None), "event_slot_with_registrations")

        # remove registration
        form=EventSlotRegistrationDeleteForm(instance=self.event_slot, user=self.user)
        form.save()

        self.assertEqual(self.event_slot.registrations.first(), None)

        # Delete slot
        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Votre évènement du lundi 1 mai 2023 de 10:00 à 12:00 a bien été supprimée'
        self.assertEqual(message, expected_message)
        self.assertEqual(EventSlot.objects.all().count(), 0)

class EventSlotRegistrationViewTestCase(EventSlotTestCase):

    def setUp(self, ):
        super().setUp()

        form = EventSlotCreateForm(data=self.form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.event_slot = form.save()

class EventSlotRegistrationCreateViewTestCase(EventSlotRegistrationViewTestCase):
    def setUp(self):
        super(EventSlotRegistrationCreateViewTestCase, self).setUp()
        self.create_url = reverse('fabcal:eventslot-register', kwargs={'pk': self.event_slot.pk})

    def test_login_required_mixin(self):
        self.assertTrue(issubclass(EventSlotRegistrationCreateView, LoginRequiredMixin))

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_event_slot_registration_create_form(self, mock_send_mail):

        form=EventSlotRegistrationCreateForm(instance=self.event_slot, user=self.user)
        event_slot = form.save()

        email_content = form.create_email_content()
        self.assertEqual(event_slot.registrations.first(), self.user)
        self.assertEqual(email_content['recipient_list'], [self.user.email])
        self.assertEqual(email_content['subject'], "Confirmation de l'inscrition à l'évènement")

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_success_message(self, mock_send_mail):
        """
        Test the get_success_message function by checking if the correct message is displayed after registering for the event.
        """
        
        self.client.login(username='user', password='userpassword')
        response = self.client.post(self.create_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = "Vous vous êtes inscrit avec succès à l'évènement my event title pendant 120 minutes le lundi 1 mai 2023 de 10:00 à 12:00"
        self.assertEqual(message, expected_message)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_dispatch_message_when_already_registered(self, mock_send_mail):
        self.client.login(username='user', password='userpassword')
        response = self.client.post(self.create_url)
        response = self.client.post(self.create_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = 'Vous êtes déjà inscrit à cet évènement !'
        self.assertEqual(message, expected_message)

class EventSlotRegistrationDeleteViewTestCase(EventSlotRegistrationViewTestCase):

    @patch('fabcal.forms.send_mail', autospec=True)
    def setUp(self, mock_send_mail):
        super(EventSlotRegistrationDeleteViewTestCase, self).setUp()

        form=EventSlotRegistrationCreateForm(instance=self.event_slot, user=self.user)
        self.event_slot = form.save()

        self.delete_url = reverse('fabcal:eventslot-unregister', kwargs={'pk': 1})

    def test_LoginRequiredMixin(self):
        self.assertTrue(issubclass(EventSlotRegistrationDeleteView, LoginRequiredMixin))
    @patch('fabcal.forms.send_mail', autospec=True)
    def test_event_slot_registration_delete_form(self, mock_send_mail):
        """
        Test the event slot registration delete form.
        """

        form=EventSlotRegistrationDeleteForm(instance=self.event_slot, user=self.user)
        form.save()

        email_content = form.create_email_content()
        self.assertEqual(self.event_slot.registrations.first(), None)
        self.assertEqual(email_content['recipient_list'], [self.user.email])
        self.assertEqual(email_content['subject'], 'Event unregistration confirmation')

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_dispatch_user_in_registrations(self, mock_send_mail):
        """
        Test case for when the user is in registrations.
        """

        self.client.login(username='user', password='userpassword')
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_dispatch_user_not_in_registrations(self, mock_send_mail):
        """
        Test case for when the user is not in registrations.
        """
        
        self.client.login(username='testsuperuser', password='testpass')
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)

    @patch('fabcal.forms.send_mail', autospec=True)
    def test_get_success_message(self, mock_send_mail):
        """
        Test the get_success_message function with a mocked send_mail function.
        """

        self.client.login(username='user', password='userpassword')

        response = self.client.post(self.delete_url)
        storage = get_messages(response.wsgi_request)
        message = [message.message for message in storage].pop()

        expected_message = "Vous vous êtes desinscrit avec succès à l'évènement my event title durant 120 minutes le lundi 1 mai 2023 de 10:00 à 12:00"
        self.assertEqual(message, expected_message)
