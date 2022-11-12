import dateparser
import datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.defaultfilters import date as _date
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe 
from django.utils.translation import gettext_lazy as _

from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot
from openings.models import Opening, Event
from machines.models import Training, TrainingNotification, Machine

class AbstractSlotForm(forms.Form):
    use_required_attribute=False
    error_css_class = 'invalid-feedback'

    start_time = forms.TimeField()
    end_time = forms.TimeField()
    comment = forms.CharField(label=_('Comment'),  required=False)

    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)

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

    def clean_start(self):
        self.cleaned_data['start'] = datetime.datetime.combine(
            dateparser.parse(self.data['date']), 
            dateparser.parse(self.data['start_time']).time()
            )

        return self.cleaned_data['start']

    def clean_end(self):
        self.cleaned_data['end'] = datetime.datetime.combine(
            dateparser.parse(self.data['date']), 
            dateparser.parse(self.data['end_time']).time()
            )
        
        return self.cleaned_data['end']

    def clean(self):
        if self.cleaned_data.get("start") and self.cleaned_data.get("end"):

            if self.cleaned_data.get("start") >= self.cleaned_data.get("end"):
                raise ValidationError(
                    _("Start time after end time.")
                )

        return self.cleaned_data

    def update_or_create_opening_slot(self, view):
        fields = [f.name for f in OpeningSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key] for key in self.cleaned_data if key in fields}

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
    machine = forms.ModelMultipleChoiceField(
        queryset = Machine.objects.filter(reservable=True),
        widget=forms.CheckboxSelectMultiple(
            attrs={'checked' : ''}
        ),
        label=_('Machines'),
        required=False
    )
    date = forms.CharField()

    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)
                
    def clean_start(self):
        super(OpeningForm, self).clean_start()

        # check if opening slot already exist / for update
        if 'opening' in self.initial:

            # check if user alread booked a modified slot
            qs = MachineSlot.objects.filter(opening_slot=OpeningSlot.objects.get(pk=self.initial['id']))

            for obj in qs:
                if obj.start < self.cleaned_data['start'] and obj.user:
                    self.validation_slot(obj)

        return self.cleaned_data['start']

    def clean_end(self):
        super(OpeningForm, self).clean_end()

        # check if opening slot already exist / for update
        if 'opening' in self.initial:

            # check if user alread booked a modified slot
            qs = MachineSlot.objects.filter(opening_slot=OpeningSlot.objects.get(pk=self.initial['id']))

            for obj in qs:
                if obj.end > self.cleaned_data['end'] and obj.user:
                    self.validation_slot(obj)

        return self.cleaned_data['end']

    def clean_machine(self):
        """Check if machine removed and already booked"""
        data = self.cleaned_data['machine']

        if 'machine' in self.initial:
            for pk in self.initial['machine']:
                if pk not in self.cleaned_data['machine'].values_list('pk', flat=True):
                    qs = MachineSlot.objects.filter(
                                opening_slot=OpeningSlot.objects.get(pk=self.initial['id']),
                                machine_id = pk
                        )
                    for obj in qs:
                        if obj.user:
                            self.validation_slot(obj)
        return data

    def validation_slot(self, obj):
        raise ValidationError(
            _('Could not update slot, %(first_name)s %(last_name)s books the slot: %(machine)s from %(start)s to %(end)s'),
            params={
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'machine': obj.machine.title,
                'start': obj.start.strftime("%H:%M"),
                'end': obj.end.strftime("%H:%M")
            } 
        )

    def create_machine_slot(self, view, machine):
        machine_slot = MachineSlot.objects.create(              
            machine= machine,
            opening_slot= view.opening_slot,
            start= self.cleaned_data['start'],
            end= self.cleaned_data['end']
        )
        return machine_slot

    def delete_machine_slot(self, view, pk):
        MachineSlot.objects.filter(opening_slot=view.opening_slot, machine_id = pk).delete()
        
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
    registration_limit = forms.IntegerField(required=True, label=_('Registration limit'))

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

        return training_slot[0]

    def alert_users(self, view): 
        
        recipient_list = [training_notification.profile.user.email for training_notification in TrainingNotification.objects.filter(training=view.context['training_slot'].training)]
        if view.crud_state == 'created':
            subject = _('A new training was planned')
            html_message = render_to_string('fabcal/email/training_create_alert.html', view.context)
        elif view.crud_state == 'updated':
            subject = _('A training was updated')
            recipient_list.extend([registration.email for registration in view.context['training_slot'].registrations.all()])
            recipient_list = set(recipient_list)
            html_message = render_to_string('fabcal/email/training_update_alert.html', view.context)
    
        send_mail(
            from_email=None,
            subject=subject,
            message = _("A new training was planned"),
            recipient_list = recipient_list,
            html_message = html_message
        )


class RegistrationTrainingForm(forms.Form):

    def register(self, view):
        training_slot = TrainingSlot.objects.get(pk=view.kwargs['pk'])
        training_slot.registrations.add(view.request.user)
        messages.success(view.request, _("Well done! We sent you an email to confirme your registration"))
    
    def send_mail(self, view):

        html_message = render_to_string('fabcal/email/training_registration_confirmation.html', view.context)
    
        send_mail(
            from_email=None,
            subject=_('Confirmation of your registration'),
            message = _("Confirmation of your registration"),
            recipient_list = [view.request.user.email],
            html_message = html_message
        )

class MachineReservationForm(forms.Form):
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    end_date = forms.CharField(required=False)
    
    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)

    def __init__(self, machine_slot, next_machine_slot, *args, **kwargs):
        super(MachineReservationForm, self).__init__(*args, **kwargs)
        self.machine_slot = machine_slot
        self.next_machine_slot = next_machine_slot

    def clean(self):

        if self.cleaned_data.get("start") and self.cleaned_data.get("end"):

            if self.cleaned_data.get("start") >= self.cleaned_data.get("end"):
                raise ValidationError(
                    _("Start time after end time.")
                )

            if self.cleaned_data['end']-self.cleaned_data['start'] < datetime.timedelta(minutes=settings.FABCAL_MINIMUM_RESERVATION_TIME):
                raise ValidationError(
                        _("Please reserve minimum %(time)s minutes !"),
                        params={'time': settings.FABCAL_MINIMUM_RESERVATION_TIME}
                    )

            if (self.cleaned_data['end']-self.cleaned_data['start']).seconds/60% settings.FABCAL_RESERVATION_INCREMENT_TIME != 0:
                raise ValidationError(
                        _("Please reserve in %(time)s minute increments !"),
                        params={'time': settings.FABCAL_MINIMUM_RESERVATION_TIME}
                    )


    def clean_start(self):
        self.cleaned_data['start'] = datetime.datetime.combine(
            self.machine_slot.start.date(), 
            dateparser.parse(self.data['start_time']).time()
            )
        
        if self.cleaned_data['start'] < self.machine_slot.start:
            raise ValidationError(
                    _("You cannot start earlier than %(start_time)s"),
                    params={'start_time': self.machine_slot.start.strftime('%H:%M')}
                )

        return self.cleaned_data['start']

    def clean_end(self):
        if self.machine_slot.machine.category.name == '3D':
            self.cleaned_data['end'] = datetime.datetime.combine( 
                dateparser.parse(self.data['end_date']).date(),
                dateparser.parse(self.data['end_time']).time()
                )
            if self.next_machine_slot:
                if self.cleaned_data['end'] > self.next_machine_slot.start:
                    raise ValidationError(
                            _("You cannot end later than %(start_time)s"),
                            params={'start_time': self.next_machine_slot.start.strftime('%H:%M')}
                        )

        else:
            self.cleaned_data['end'] = datetime.datetime.combine( 
                self.machine_slot.end.date(),
                dateparser.parse(self.data['end_time']).time()
                )
        
            if self.cleaned_data['end'] > self.machine_slot.end:
                raise ValidationError(
                        _("You cannot end later than %(start_time)s"),
                        params={'start_time': self.machine_slot.end.strftime('%H:%M')}
                    )
        
        return self.cleaned_data['end']

    def send_mail(self, view):
        html_message = render_to_string('fabcal/email/machine_reservation_confirmation.html', view.context)
    
        send_mail(
            from_email=None,
            subject=_('Confirmation of your machine reservation'),
            message = _("Confirmation of your machine reservation"),
            recipient_list = [view.request.user.email],
            html_message = html_message
        )

    def message(self, view):
        return messages.success(
            view.request,
            _('You successfully booked the machine ') + 
            self.machine_slot.machine.title + 
            _(" on ") +
            self.machine_slot.start.strftime('%A %d %B') +
            _(" from ") +
            self.machine_slot.start.strftime('%H:%M')+
            _(" to ") +
            self.machine_slot.end.strftime('%H:%M')
            )