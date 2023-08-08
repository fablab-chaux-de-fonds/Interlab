import datetime
import re

from django.contrib.auth.models import Group, AnonymousUser
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, HttpResponse
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils.translation import activate
from django.views import View

from accounts.models import CustomUser
from openings.models import Opening
from fabcal.forms import OpeningSlotForm
from fabcal.models import OpeningSlot
from machines.models import Machine

from .views import OpeningSlotCreateView, OpeningSlotUpdateView
from .mixins import SuperuserRequiredMixin

class TestView(SuperuserRequiredMixin, View):
    def get(self, request):
        self.request = request
        return HttpResponse('Success')

class SuperuserRequiredMixinTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.login_url = reverse('login')  # Replace 'login' with the actual URL name

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

class OpeningSlotViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.create_url = reverse('fabcal:openingslot-create') + '?start=1682784000000&end=1682791200000'

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

class OpeningSlotCreateViewTestCase(OpeningSlotViewTestCase):
    def setUp(self):
        super().setUp()

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(OpeningSlotCreateView, SuperuserRequiredMixin))

    def test_save_method(self):
        request = self.factory.post(self.create_url, self.get_default_form_data())
        request.user = self.superuser
        view = OpeningSlotCreateView()
        view.setup(request)
        form = view.get_form()
        self.assertTrue(form.is_valid())

        form.save()
        
        # Assertions for the instance attributes
        self.assertEqual(form.instance.user, self.superuser)
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
        self.client.login(username='testsuperuser', password='testpass')

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
        self.assertEqual(response.status_code, 302)

        self.assertIn('/schedule/', response.url)
        
        obj = OpeningSlot.objects.latest('id')
        self.assertEqual(obj.start, datetime.datetime(2023, 5, 1, 10, 0))
        self.assertEqual(obj.end, datetime.datetime(2023, 5, 1, 12, 0))
        self.assertEqual(obj.comment, 'my comment')
        self.assertEqual(obj.user, self.superuser)
        self.assertEqual(obj.get_machine_list, [self.trotec])
        self.assertEqual(obj.opening, self.openlab)

    def test_get_success_message(self):
        # activate('fr')
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

    def tearDown(self):
        self.client.logout()
        self.superuser.delete()
        self.group.delete()

class OpeningSlotUpdateViewTestCase(OpeningSlotViewTestCase):
    def setUp(self):
        super().setUp()
        self.update_url = reverse('fabcal:openingslot-update', kwargs={'pk': 1})

    def test_SuperuserRequiredMixin(self):
        self.assertTrue(issubclass(OpeningSlotUpdateView, SuperuserRequiredMixin))