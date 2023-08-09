import datetime

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from accounts.models import CustomUser
from .models import OpeningSlot, Opening, MachineSlot, Machine
from .tasks import remove_openingslot_if_on_reservation


class OpeningSlotViewTestCase(TestCase):

    def setUp(self):
        self.openlab = Opening.objects.create(
            title='OpenLab', 
            is_open_to_reservation=True, 
            is_open_to_questions=True,
            is_reservation_mandatory=True,
            is_public=True
            )
        
        self.trotec = Machine.objects.create(
            title = 'Trotec'
        )

    def test_remove_openingslot_if_on_reservation(self):
        # Create an opening slot without reservations within the next 24 hours
        start = datetime.datetime.now() + datetime.timedelta(hours=1)
        end = start + datetime.timedelta(hours=2)

        opening_slot = OpeningSlot.objects.create(
            opening=self.openlab,
            start=start,
            end=end
        )

        MachineSlot.objects.create(
            opening_slot=opening_slot,
            machine=self.trotec,
            start=start,
            end=end
        )

        # Call the function to remove opening slots without reservations
        remove_openingslot_if_on_reservation()

        # Check that the opening slot was removed
        self.assertEqual(OpeningSlot.objects.count(), 0)

    def test_remove_openingslot_with_user(self):
        # Create an opening slot without reservations within the next 24 hours
        start = datetime.datetime.now() + datetime.timedelta(hours=1)
        end = start + datetime.timedelta(hours=2)
        opening_slot = OpeningSlot.objects.create(
            opening=self.openlab,
            start=start,
            end=end
        )

        # Create a user and associate it with a MachineSlot
        user = CustomUser.objects.create_user(username='testuser', password='testpass')
        MachineSlot.objects.create(
            opening_slot=opening_slot,
            machine=self.trotec,
            start=start,
            end=end,
            user=user
        )

        # Call the function to remove opening slots without reservations
        remove_openingslot_if_on_reservation()

        # Check that the opening slot was not removed due to the associated user
        self.assertEqual(OpeningSlot.objects.count(), 1)