from django.test import TestCase
from .models import Opening, Event
class ReprTestCase(TestCase):
    def setUp(self):
        Opening.objects.create(
            title='opening title',
            is_open_to_reservation = False,
            is_open_to_questions = False,
            is_reservation_mandatory = False,
            is_public = False
        )
        Event.objects.create(
            title = 'event title', 
            is_on_site = False, 
            is_active = False
        )

    def test_repr(self):
        self.assertEqual(Opening.objects.all().first().__str__(), 'opening title')
        self.assertEqual(Event.objects.all().first().__str__(), 'event title')