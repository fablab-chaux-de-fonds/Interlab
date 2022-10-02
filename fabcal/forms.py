import dateparser
import datetime

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.template.defaultfilters import date as _date
from django.utils.safestring import mark_safe 
from django.utils.translation import gettext_lazy as _

from .models import OpeningSlot, EventSlot
from openings.models import Opening, Event

class AbstractSlotForm(forms.Form):
    use_required_attribute=False
    error_css_class = 'invalid-feedback'

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)

    class Meta:
        abstract = True

    def update_or_create_opening_slot(self, view):
        fields = [f.name for f in OpeningSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key]  for key in self.cleaned_data if key in fields}

        OpeningSlot.objects.update_or_create(
            # Refactor - add update
            pk = None,
            defaults = defaults
            )

        messages.success(view.request, mark_safe(
            _("Your openings has been successfully %(crud_state)s on ") % {'crud_state': _(view.crud_state)} + 
            _date(self.cleaned_data['start'], "l d F Y") + 
            _(" from ") +
            self.cleaned_data['start'].strftime("%H:%M") + 
            _(" to ") + 
            self.cleaned_data['end'].strftime("%H:%M") + 
            "</br>" +
            "<a href=\"/fabcal/download-ics-file/" + self.cleaned_data['opening'].title + "/" + self.cleaned_data['start'].strftime("%Y%m%dT%H%M%S%z")  + "/" + self.cleaned_data['end'].strftime("%Y%m%dT%H%M%S%z")  + "/\" download>" + 
            "<i class=\"bi bi-file-earmark-arrow-down-fill\"></i> " + 
            _('Download .ICS file') +
            "</a>"
            )
        )
class OpeningForm(AbstractSlotForm):
    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('Select an opening'),
        error_messages={'required': _('Please select an opening.')}
        )
    date = forms.CharField()
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    comment = forms.CharField(label=_('Comment'),  required=False)

    def clean(self):
        self.cleaned_data = super().clean()

        self.cleaned_data['start'] = datetime.datetime.combine(
            dateparser.parse(self.cleaned_data['date']), 
            self.cleaned_data['start_time']
            )
        
        self.cleaned_data['end'] = datetime.datetime.combine(
            dateparser.parse(self.cleaned_data['date']), 
            self.cleaned_data['end_time']
            )

        if self.cleaned_data.get("start") >= self.cleaned_data.get("end"):
            raise ValidationError(
                _("Start time after end time.")
            )
        
class EventForm(AbstractSlotForm):
    event = forms.ModelChoiceField(
        queryset= Event.objects.filter(is_active=True),
        label=_('Event'),
        empty_label=_('Select an event'),
        error_messages={'required': _('Please select an event.')}, 
        )
    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('No opening'),
        required=False,
        )
    start_date = forms.CharField()
    start_time = forms.TimeField()
    end_date = forms.CharField()
    end_time = forms.TimeField()
    price = forms.CharField(label=_('Price'), widget=forms.Textarea(attrs={'class':'form-control', 'rows':4}))
    comment = forms.CharField(label=_('Comment'),  required=False)
    has_registration = forms.BooleanField(required=False, label=_('On registration'))
    registration_limit = forms.IntegerField(required=False, label=_('Registration limit'), help_text=_('leave blank if no limit'))


    def clean(self):
        self.cleaned_data = super().clean()

        self.cleaned_data['start'] = datetime.datetime.combine(
            dateparser.parse(self.cleaned_data['start_date']), 
            self.cleaned_data['start_time']
            )
        
        self.cleaned_data['end'] = datetime.datetime.combine(
            dateparser.parse(self.cleaned_data['end_date']), 
            self.cleaned_data['end_time']
            )

        if self.cleaned_data.get("start") >= self.cleaned_data.get("end"):
            raise ValidationError(
                _("Start date after end date.")
            )

    def update_or_create_event_slot(self, view):
        fields = [f.name for f in EventSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key]  for key in self.cleaned_data if key in fields}

        EventSlot.objects.update_or_create(
            # Refactor - add update
            pk = None,
            defaults = defaults
            )
        
        messages.success(view.request, mark_safe(
            _("Your event has been successfully %(crud_state)s on ") % {'crud_state': _(view.crud_state)} + 
            _date(self.cleaned_data['start'], "l d F Y") + 
            _(" from ") +
            self.cleaned_data['start'].strftime("%H:%M") + 
            _(" to ") + 
            self.cleaned_data['end'].strftime("%H:%M") + 
            "</br>" +
            "<a href=\"/fabcal/download-ics-file/" + self.cleaned_data['event'].title + "/" + self.cleaned_data['start'].strftime("%Y%m%dT%H%M%S%z")  + "/" + self.cleaned_data['end'].strftime("%Y%m%dT%H%M%S%z")  + "/\" download>" + 
            "<i class=\"bi bi-file-earmark-arrow-down-fill\"></i> " + 
            _('Download .ICS file') +
             "</a>"
            )
        )

