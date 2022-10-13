import dateparser
import datetime

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.template.defaultfilters import date as _date
from django.utils.safestring import mark_safe 
from django.utils.translation import gettext_lazy as _

from .models import OpeningSlot, EventSlot, TrainingSlot    
from openings.models import Opening, Event
from machines.models import Training

class AbstractSlotForm(forms.Form):
    use_required_attribute=False
    error_css_class = 'invalid-feedback'

    start_time = forms.TimeField()
    end_time = forms.TimeField()
    comment = forms.CharField(label=_('Comment'),  required=False)

    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('No opening'),
        required=False,
        )

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
    class Meta:
        abstract = True

    def clean(self):
        self.cleaned_data = super(AbstractSlotForm, self).clean()

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

    def update_or_create_opening_slot(self, view):
        fields = [f.name for f in OpeningSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key]  for key in self.cleaned_data if key in fields}

        opening_slot = OpeningSlot.objects.update_or_create(
            pk = view.kwargs.get('pk', None),
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

        return opening_slot[0]
class OpeningForm(AbstractSlotForm):
    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('Select an opening'),
        error_messages={'required': _('Please select an opening.')}
        )
    date = forms.CharField()
        
class EventForm(AbstractSlotForm):
    event = forms.ModelChoiceField(
        queryset= Event.objects.filter(is_active=True),
        label=_('Event'),
        empty_label=_('Select an event'),
        error_messages={'required': _('Please select an event.')}, 
        )
    start_date = forms.CharField()
    end_date = forms.CharField()
    price = forms.CharField(label=_('Price'), widget=forms.Textarea(attrs={'class':'form-control', 'rows':4}))
    has_registration = forms.BooleanField(required=False, label=_('On registration'))
    registration_limit = forms.IntegerField(required=False, label=_('Registration limit'), help_text=_('leave blank if no limit'))


    def clean(self):
        self.cleaned_data = super(AbstractSlotForm, self).clean()

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

    def update_or_create_event_slot(self, view, opening_slot):
        fields = [f.name for f in EventSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key]  for key in self.cleaned_data if key in fields}
        defaults['opening_slot'] = opening_slot

        EventSlot.objects.update_or_create(
            pk = view.kwargs.get('pk', None),
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

class TrainingForm(AbstractSlotForm):
    training = forms.ModelChoiceField(
        queryset= Training.objects.filter(is_active=True),
        label=_('Training'),
        empty_label=_('Select a training'),
        error_messages={'required': _('Please select a training.')}, 
        )
    date = forms.CharField()

    def update_or_create_training_slot(self, view,opening_slot):
        fields = [f.name for f in TrainingSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key]  for key in self.cleaned_data if key in fields}
        defaults['opening_slot'] = opening_slot

        training_slot = TrainingSlot.objects.update_or_create(
            pk = view.kwargs.get('pk', None),
            defaults = defaults
            )

        messages.success(view.request, mark_safe(
            _("Your trainings has been successfully %(crud_state)s on ") % {'crud_state': _(view.crud_state)} + 
            _date(self.cleaned_data['start'], "l d F Y") + 
            _(" from ") +
            self.cleaned_data['start'].strftime("%H:%M") + 
            _(" to ") + 
            self.cleaned_data['end'].strftime("%H:%M") + 
            "</br>" +
            "<a href=\"/fabcal/download-ics-file/" + self.cleaned_data['training'].title + "/" + self.cleaned_data['start'].strftime("%Y%m%dT%H%M%S%z")  + "/" + self.cleaned_data['end'].strftime("%Y%m%dT%H%M%S%z")  + "/\" download>" + 
            "<i class=\"bi bi-file-earmark-arrow-down-fill\"></i> " + 
            _('Download .ICS file') +
            "</a>"
            )
        )