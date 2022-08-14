from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .models import OpeningSlot, EventSlot

class OpeningForm(ModelForm):
    class Meta:
        model = OpeningSlot
        fields = ['opening', 'start', 'end', 'comment']
        
class EventForm(ModelForm):
    class Meta:
        model = EventSlot
        fields = ['event', 'price', 'start', 'end', 'has_registration', 'registration_limit', 'opening', 'comment']

        def clean_event(self):
            data = self.cleaned_data['event']
        