import datetime
import dateparser
from babel.dates import format_datetime, get_timezone

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe 
from django.utils.translation import gettext_lazy as _

from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot
from openings.models import Opening, Event
from machines.models import Training, TrainingNotification, Machine
from .custom_fields import CustomDateField

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

    machine = forms.ModelMultipleChoiceField(
        queryset = Machine.objects.filter(reservable=True),
        widget=forms.CheckboxSelectMultiple(
            attrs={'checked' : ''}
        ),
        label=_('Machines'),
        required=False
    )

    def __init__(self, *args, **kwargs):
        kwargs["label_suffix"] = ""
        super().__init__(*args, **kwargs)
    class Meta:
        abstract = True

    def clean_start(self):
        if 'date' in self.data:
            # for Trainings and Openings
            start_date = self.data['date']
        elif 'start_date' in self.data:
            # for Events
            start_date = self.data['start_date']
        else:
            # for Machines
            start_date = format_datetime(self.cleaned_data['start'], "EEEE d MMMM y", locale=settings.LANGUAGE_CODE)

        self.cleaned_data['start'] = datetime.datetime.combine(
            dateparser.parse(start_date), 
            dateparser.parse(self.data['start_time']).time()
            )

        # check if opening slot already exist / for update
        if 'opening' in self.initial:

            # check if user alread booked a modified slot
            qs = MachineSlot.objects.filter(opening_slot=OpeningSlot.objects.get(pk=self.initial['id']))

            for obj in qs:
                if obj.start < self.cleaned_data['start'] and obj.user:
                    self.validation_slot(obj)

        return self.cleaned_data['start']

    def clean_end(self):
        if 'date' in self.data:
            # for Trainings and Openings
            end_date = self.data['date']
        elif 'end_date' in self.data:
            # for Events
            end_date = self.data['end_date']
        else:
            # for Machines
            end_date = format_datetime(self.cleaned_data['end'], "EEEE d MMMM y", locale=settings.LANGUAGE_CODE)

        self.cleaned_data['end'] = datetime.datetime.combine(
            dateparser.parse(end_date), 
            dateparser.parse(self.data['end_time']).time()
            )

        # check if opening slot already exist / for update
        if 'opening' in self.initial:

            # check if user alread booked a modified slot
            qs = MachineSlot.objects.filter(opening_slot=OpeningSlot.objects.get(pk=self.initial['id']))

            for obj in qs:
                if obj.end > self.cleaned_data['end'] and obj.user:
                    self.validation_slot(obj)
        
        return self.cleaned_data['end']

    def clean(self):
        if self.cleaned_data.get("start") and self.cleaned_data.get("end"):

            if self.cleaned_data.get("start") >= self.cleaned_data.get("end"):
                raise ValidationError(
                    _("Start time after end time.")
                )

        return self.cleaned_data

    def update_or_create_opening_slot(self, view):
        fields = [f.name for f in OpeningSlot._meta.get_fields()]
        defaults = {key: self.cleaned_data[key] for key in self.cleaned_data if key in fields}
        defaults['user'] = view.request.user

        opening_slot = OpeningSlot.objects.update_or_create(
            pk = view.kwargs.get('pk', None),
            defaults = defaults
            )

        context = {
            'crud_state': "créée" if view.crud_state == "created" else "mise à jour",
            'start_date': format_datetime(self.cleaned_data['start'], "EEEE d MMMM y", locale=settings.LANGUAGE_CODE),
            'start_time': format_datetime(self.cleaned_data['start'], "H:mm", locale=settings.LANGUAGE_CODE), 
            'end_time': format_datetime(self.cleaned_data['end'], "H:mm", locale=settings.LANGUAGE_CODE),
            'opening_title': self.cleaned_data['opening'].title,
            'start': self.cleaned_data['start'].isoformat(),
            'end': self.cleaned_data['end'].isoformat()
        }
        
        messages.success(
            view.request,
            mark_safe(_('Your openings has been successfully %(crud_state)s on %(start_date)s from %(start_time)s to %(end_time)s</br><a href="/fabcal/download-ics-file/%(opening_title)s/%(start)s/%(end)s"><i class="bi bi-file-earmark-arrow-down-fill"></i> Add to my calendar</a>')
            % context))

        return opening_slot[0]

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

class OpeningSlotForm(ModelForm):
    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('Select an opening'),
        error_messages={'required': _('Please select an opening.')}
        )
    date = CustomDateField()
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    comment = forms.CharField(label=_('Comment'),  required=False)

    class Meta:
        model = OpeningSlot
        fields = ('opening', 'date', 'start_time', 'end_time', 'comment')

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

    def clean_start(self):
        self.cleaned_data['start'] = datetime.datetime.combine(
            dateparser.parse(self.data['start_date']), 
            self.cleaned_data['start_time']
            )
        return self.cleaned_data['start']
        
    def clean_end(self): 
        self.cleaned_data['end'] = datetime.datetime.combine(
            dateparser.parse(self.data['end_date']), 
            self.cleaned_data['end_time']
            )
        return self.cleaned_data['end']

    def update_or_create_event_slot(self, view):
        fields = [f.name for f in EventSlot._meta.get_fields()] + ['user_id']
        defaults = {key: self.cleaned_data[key]  for key in self.cleaned_data if key in fields}
        defaults['user'] = view.request.user
        
        if hasattr(view, 'opening_slot'):
            defaults['opening_slot'] = view.opening_slot

        EventSlot.objects.update_or_create(
            pk = view.kwargs.get('pk', None),
            defaults = defaults
            )

        context = {
            'crud_state': "créé" if view.crud_state == "created" else "mise à jour",
            'start_date': format_datetime(self.cleaned_data['start'], "EEEE d MMMM y", locale=settings.LANGUAGE_CODE),
            'start_time': format_datetime(self.cleaned_data['start'], "H:mm", locale=settings.LANGUAGE_CODE), 
            'end_time': format_datetime(self.cleaned_data['end'], "H:mm", locale=settings.LANGUAGE_CODE),
            'event_title': self.cleaned_data['event'].title,
            'start': self.cleaned_data['start'].isoformat(),
            'end': self.cleaned_data['end'].isoformat()
        }
        
        messages.success(
            view.request,
            mark_safe(_('Your event has been successfully %(crud_state)s on %(start_date)s from %(start_time)s to %(end_time)s</br><a href="/fabcal/download-ics-file/%(event_title)s/%(start)s/%(end)s"><i class="bi bi-file-earmark-arrow-down-fill"></i> Add to my calendar</a>')
            % context))

class TrainingForm(AbstractSlotForm):
    training = forms.ModelChoiceField(
        queryset= Training.objects.filter(is_active=True),
        label=_('Training'),
        empty_label=_('Select a training'),
        error_messages={'required': _('Please select a training.')}
        )
    date = forms.CharField()
    registration_limit = forms.IntegerField(required=True, label=_('Registration limit'))

    def update_or_create_training_slot(self, view):
        fields = [f.name for f in TrainingSlot._meta.get_fields()]
        defaults = {key: self.cleaned_data[key] for key in self.cleaned_data if key in fields}
        defaults['user'] = view.request.user

        if hasattr(view, 'opening_slot'):
            defaults['opening_slot'] = view.opening_slot

        training_slot = TrainingSlot.objects.update_or_create(
            pk = view.kwargs.get('pk', None),
            defaults = defaults
            )

        context = {
            'crud_state': "créée" if view.crud_state == "created" else "mise à jour",
            'start_date': format_datetime(self.cleaned_data['start'], "EEEE d MMMM y", locale=settings.LANGUAGE_CODE),
            'start_time': format_datetime(self.cleaned_data['start'], "H:mm", locale=settings.LANGUAGE_CODE), 
            'end_time': format_datetime(self.cleaned_data['end'], "H:mm", locale=settings.LANGUAGE_CODE),
            'training_title': self.cleaned_data['training'].title,
            'start': self.cleaned_data['start'].isoformat(),
            'end': self.cleaned_data['end'].isoformat()
        }
        
        messages.success(
            view.request,
            mark_safe(_('Your training has been successfully %(crud_state)s on %(start_date)s from %(start_time)s to %(end_time)s</br><a href="/fabcal/download-ics-file/%(training_title)s/%(start)s/%(end)s"><i class="bi bi-file-earmark-arrow-down-fill"></i> Add to my calendar</a>')
            % context))

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

class RegisterEventForm(forms.Form):
    pass

class RegisterTrainingForm(forms.Form):
    pass

class MachineReservationForm(AbstractSlotForm):
    end_date = forms.CharField(required=False)

    def __init__(self, machine_slot, next_machine_slot, previous_machine_slot, *args, **kwargs):
        super(MachineReservationForm, self).__init__(*args, **kwargs)
        self.machine_slot = machine_slot
        self.next_machine_slot = next_machine_slot
        self.previous_machine_slot = previous_machine_slot

    def clean(self):
        super(MachineReservationForm, self).clean()

        if self.cleaned_data.get("start") and self.cleaned_data.get("end"):
            
            self.cleaned_data['duration'] = self.cleaned_data['end']-self.cleaned_data['start']
            if self.cleaned_data['duration'] < datetime.timedelta(minutes=settings.FABCAL_MINIMUM_RESERVATION_TIME):
                raise ValidationError(
                        _("Please reserve minimum %(time)s minutes !"),
                        params={'time': settings.FABCAL_MINIMUM_RESERVATION_TIME}
                    )

            if (self.cleaned_data['duration']).seconds/60 % settings.FABCAL_RESERVATION_INCREMENT_TIME != 0:
                raise ValidationError(
                        _("Please reserve in %(time)s minute increments !"),
                        params={'time': settings.FABCAL_MINIMUM_RESERVATION_TIME}
                    )
            if self.previous_machine_slot:
                if self.previous_machine_slot.end > self.cleaned_data['start']:
                        raise ValidationError(
                            _("The machine is already booked until %(time)s !"),
                            params={'time': self.previous_machine_slot.end.strftime('%H:%M')}
                    )

            if self.next_machine_slot:
                if self.next_machine_slot.start < self.cleaned_data['end']:
                        raise ValidationError(
                            _("The machine is already booked from %(time)s !"),
                            params={'time': self.next_machine_slot.start.strftime('%H:%M')}
                        )

    def clean_start(self):
        self.cleaned_data['start'] = datetime.datetime.combine(
            self.machine_slot.start.date(), 
            dateparser.parse(self.data['start_time']).time()
            )
        
        if self.cleaned_data['start'] < self.machine_slot.opening_slot.start:
            raise ValidationError(
                    _("You cannot start earlier than %(start_time)s"),
                    params={'start_time': self.machine_slot.opening_slot.start.strftime('%H:%M')}
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
        
            if self.cleaned_data['end'] > self.machine_slot.opening_slot.end:
                raise ValidationError(
                        _("You cannot end later than %(start_time)s"),
                        params={'start_time': self.machine_slot.opening_slot.end.strftime('%H:%M')}
                    )
        
        return self.cleaned_data['end']