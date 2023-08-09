import datetime

from django.core import mail
from django.contrib.auth.models import Group
from django.test import TestCase, Client, RequestFactory, override_settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from accounts.models import CustomUser
from .models import OpeningSlot, Opening, MachineSlot, Machine
from .tasks import remove_openingslot_if_on_reservation

class OpeningSlotViewTestCase(TestCase):

    def setUp(self):

        # Create a superuser and add them to the 'superuser' group
        self.superuser = CustomUser.objects.create_user(
            username='testsuperuser',
            password='testpass',
            email='superuser@fake.django'
            )
        self.group = Group.objects.get_or_create(name='superuser')[0]
        self.superuser.groups.add(self.group)
        
        # Create opening
        self.openlab = Opening.objects.create(
            title='OpenLab', 
            is_open_to_reservation=True, 
            is_open_to_questions=True,
            is_reservation_mandatory=True,
            is_public=True
            )

        # Create machine        
        self.trotec = Machine.objects.create(
            title = 'Trotec'
        )

        # Create an opening slot without reservations within the next 24 hours
        self.start = datetime.datetime.now() + datetime.timedelta(days=1, minutes=1)
        self.end = self.start + datetime.timedelta(hours=2)

        self.opening_slot = OpeningSlot.objects.create(
            opening=self.openlab,
            start=self.start,
            end=self.end,
            user = self.superuser
        )

    def test_remove_openingslot_if_on_reservation(self):
        MachineSlot.objects.create(
            opening_slot=self.opening_slot,
            machine=self.trotec,
            start=self.start,
            end=self.end
        )

        # Call the function to remove opening slots without reservations
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            remove_openingslot_if_on_reservation()
        
        # Check if an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Assert the email details
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, _('No reservation - your opening slot has been deleted'))

        # Assert the email recipient
        self.assertEqual(sent_email.to, [self.superuser.email])

        # Check that the opening slot was removed
        self.assertEqual(OpeningSlot.objects.count(), 0)

    def test_remove_openingslot_with_user(self):
        # Create a user and associate it with a MachineSlot
        user = CustomUser.objects.create_user(username='testuser', password='testpass')
        MachineSlot.objects.create(
            opening_slot=self.opening_slot,
            machine=self.trotec,
            start=self.start,
            end=self.end,
            user=user
        )

        # Call the function to remove opening slots without reservations
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            remove_openingslot_if_on_reservation()
        
        # Check if an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Assert the email details
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, _('You have reservation - your opening slot is confirmed'))

        # Assert the email recipient
        self.assertEqual(sent_email.to, [self.superuser.email])

        # Check that the opening slot was not removed due to the associated user
        self.assertEqual(OpeningSlot.objects.count(), 1)