import datetime
import dateparser
import os

from babel.dates import format_datetime, get_timezone
from copy import deepcopy

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe 
from django.utils.translation import gettext_lazy as _

from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot
from openings.models import Opening, Event
from machines.models import Training, TrainingNotification, Machine
from .custom_fields import CustomDateField
from .validators import validate_delete_machine_slot

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
            'start': self.cleaned_data['start'].strftime("%Y%m%dT%H%M%SZ"),
            'end': self.cleaned_data['end'].strftime("%Y%m%dT%H%M%SZ")
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

class UserForm(ModelForm):
    def __init__(self, user=None,  *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user

class SlotForm(UserForm):
    date = CustomDateField(required=False)
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    comment = forms.CharField(label=_('Comment'),  required=False)

    def clean(self):
        cleaned_data = super(SlotForm, self).clean()
        date = cleaned_data.get('date') or self.instance.start.date()
        start_time = cleaned_data.get('start_time') or self.instance.start.time()
        end_time = cleaned_data.get('end_time') or self.instance.end.time()

        # set the start and end fields of the instance
        self.cleaned_data['start'] = datetime.datetime.combine(date, start_time)
        self.cleaned_data['end'] = datetime.datetime.combine(date, end_time)

        # update instance before clean in model
        self.instance.start = self.cleaned_data['start']
        self.instance.end = self.cleaned_data['end']

        return cleaned_data

class OpeningSlotForm(SlotForm):
    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('Select an opening'),
        error_messages={'required': _('Please select an opening.')}
        )

    machines = forms.ModelMultipleChoiceField(
        queryset = Machine.objects.filter(reservable=True),
        widget=forms.CheckboxSelectMultiple(
            attrs={'checked' : ''}
        ),
        label=_('Machines'),
        required=False
    )

    class Meta:
        model = OpeningSlot
        fields = ('opening', 'machines', 'date', 'start_time', 'end_time', 'comment')

    def save(self):
        self.instance.user = self.user
        return self.instance

class SlotLinkedToOpeningForm(OpeningSlotForm):
    opening = forms.ModelChoiceField(
        queryset=Opening.objects.all(),
        label=_('Opening'),
        empty_label=_('Select an opening'),
        required=False
        )

    registration_limit = forms.IntegerField(required=True, label=_('Registration limit'))

    def save(self, opening_slot_form_class, initial=None):
        """
        Save the opening slot form data and send mail with the created instance.

        Parameters:
            opening_slot_form_class (class): The class of the opening slot form.

        Returns:
            instance: The created instance.
        """
        self.instance = super().save()

        opening_data = self.cleaned_data.get('opening')

        if opening_data:
            form_data = {
                'opening':opening_data,
                'machines':self.cleaned_data.get('machines'),
                'date':self.cleaned_data.get('date'),
                'start_time':self.cleaned_data.get('start_time'),
                'end_time':self.cleaned_data.get('end_time'),
                'comment':self.cleaned_data.get('comment')
            }

            form = opening_slot_form_class(
                data=form_data,
                initial=initial,
                instance=self.instance.opening_slot,
            )

            form.is_valid()
            opening_slot = form.save()
        
            self.instance.opening_slot = opening_slot
        
        self.instance.save()

        return self.instance

class OpeningSlotCreateForm(OpeningSlotForm):

    def save(self):
        self.instance = super().save()
        self.instance.save()

        for machine in self.cleaned_data['machines']:
            MachineSlot.objects.create(              
                machine=machine,
                opening_slot=self.instance,
                start=self.instance.start,
                end=self.instance.end
            )

        return self.instance

class OpeningSlotUpdateForm(OpeningSlotForm):

    def clean(self):
        machines_to_remove = set(self.initial.get('machines', [])) - set(self.cleaned_data['machines'].values_list('pk', flat=True))

        for pk in machines_to_remove:
            machine_slot = MachineSlot.objects.get(opening_slot=self.instance, machine=pk)
            validate_delete_machine_slot(machine_slot)

        return super().clean()

    def save(self):
        self.instance = super().save()
        self.instance.save()

        # -------------------
        # Remove machine slot
        machines_to_remove = set(self.initial.get('machines', [])) - set(self.cleaned_data['machines'].values_list('pk', flat=True))

        for pk in machines_to_remove:
            machine_slot = MachineSlot.objects.get(opening_slot=self.instance, machine=pk)
            machine_slot.delete()

        # -------------------
        # Update or create machine slot

        for machine in self.cleaned_data['machines']:

            # Get the machine slots to update.
            qs = MachineSlot.objects.filter(
                opening_slot=self.instance,
                machine=machine
            ).order_by('start')

            # Update the start slots.
            if self.instance.start < self.initial['start']:
                # Extend start opening before.
                obj = qs.first()
                if obj.user:
                    # Create a new slot to not modify user reservation.
                    MachineSlot.objects.create(
                        opening_slot=self.instance,
                        machine=machine,
                        start=self.instance.start,
                        end=self.initial['start']
                    )
                else:
                    # Extend slot.
                    obj.start = self.instance.start
                    obj.save()

            # Shorten or remove start slots.
            if self.instance.start > self.initial['start']:
                for obj in qs:
                    if obj.start < self.instance.start:
                        if obj.end > self.instance.start:
                            # Shorten start slot.
                            obj.start = self.instance.start
                            obj.save()
                        else:
                            # Remove start slot.
                            obj.delete()

            # Update the end slots.
            if self.instance.end < self.initial['end']:
                # Shorten or remove end slots.
                for obj in qs:
                    if obj.end > self.instance.end:
                        if obj.start < self.instance.end:
                            # Shorten end slot.
                            obj.end = self.instance.end
                            obj.save()
                        else:
                            # Remove end slot.
                            obj.delete()

            if self.instance.end > self.initial['end']:
                # Extend end opening after.
                obj = qs.last()
                if obj.user:
                    # Create a new slot to not modify user reservation.
                    MachineSlot.objects.create(
                        opening_slot=self.instance,
                        machine=machine,
                        start=self.initial['end'],
                        end=self.instance.end
                    )
                else:
                    # Extend slot.
                    obj.end = self.instance.end
                    obj.save()

            # Create a new machine slot
            if machine.pk not in self.initial.get('machines', []):
                MachineSlot.objects.create(
                        opening_slot=self.instance,
                        machine=machine,
                        start=self.instance.start,
                        end=self.instance.end
                    )

        return self.instance

class MachineSlotUpdateForm(SlotForm):
    end_date = forms.CharField(required=False)

    class Meta:
        model = MachineSlot
        fields = ('start_time', 'end_time')

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')

        if self.cleaned_data['start_time'] < self.instance.opening_slot.start.time():
            raise ValidationError(
                    _("You cannot start earlier than %(start_time)s"),
                    params={'start_time': self.instance.start.time().strftime('%H:%M')},
                    code='invalid_start_time'
                )
                
        return start_time

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')

        # Check if end time is later than opening slot end time
        if self.cleaned_data['end_time'] > self.instance.opening_slot.end.time():
            raise ValidationError(
                    _("You cannot end later than %(end_time)s"),
                    params={'end_time': self.instance.end.time().strftime('%H:%M')},
                    code='invalid_end_time'
                )

        return end_time

    def clean_end(self):
        """
        This method checks if the machine category is '3D' and ensures that the 'end' time does not exceed the start time
        of the next slot, if it exists.

        Raises:
            ValidationError: If the 'end' time is later than the start time of the next slot, a ValidationError is raised.

        Returns:
            datetime.time: The cleaned 'end' time.
        """
        machine_category = self.instance.machine.category.name

        if machine_category == '3D' and self.instance.next_slot:
            end_time = self.cleaned_data['end']
            next_slot_start_time = self.instance.next_slot.start

            if end_time > next_slot_start_time:
                raise ValidationError(
                    _("You cannot end later than %(start_time)s"),
                    params={'start_time': next_slot_start_time.strftime('%H:%M')}
                )

        return self.cleaned_data['end']

    def clean(self):
        """
        A method to clean and validate the form data. 
        
        It checks the start and end time, calculates the duration, and validates the reservation time and duration increment.
        It also checks for overlapping reservations in the case of a 3D print reservation. 
        
        Returns the cleaned data.
        """
        cleaned_data = super().clean()
        initial_machine_slot = MachineSlot.objects.get(pk=self.instance.pk)
        start_time = self.cleaned_data.get("start")
        end_time = self.cleaned_data.get("end")

        # Check if end datetime is sooner than the initial end datetime
        if self.cleaned_data['start'] < self.initial.get('start', self.cleaned_data['start']):
            # check if previous slots are free until slef.cleaned_data['start_time']
            until = self.cleaned_data['start']
            machine_slots_to_check = initial_machine_slot.previous_slots(until)

            for machine_slot in machine_slots_to_check:
                if machine_slot.user and machine_slot.user != self.instance.user:
                    raise ValidationError(
                        _("The machine is already booked until %(time)s!"),
                        params={'time': machine_slot.start.strftime('%H:%M')},
                        code='machine_slot_already_booked'
                    )

        # Check if end datetime is later than the initial end datetime
        if self.cleaned_data['end'] > self.initial.get('end', self.cleaned_data['end']):
            # check if next slots are free until slef.cleaned_data['end_time']
            until = self.cleaned_data['end']
            machine_slots_to_check = initial_machine_slot.next_slots(until)

            for machine_slot in machine_slots_to_check:
                if machine_slot.user and machine_slot.user != self.instance.user:
                    raise ValidationError(
                        _("The machine is already booked from %(time)s!"),
                        params={'time': machine_slot.start.strftime('%H:%M')},
                        code='machine_slot_already_booked'
                    )

        if start_time and end_time: 
            cleaned_data['duration'] = end_time - start_time

            if cleaned_data['duration'] < datetime.timedelta(minutes=settings.FABCAL_MINIMUM_RESERVATION_TIME):
                raise ValidationError(
                    _("Please reserve a minimum of %(time)s minutes!"),
                    params={'time': settings.FABCAL_MINIMUM_RESERVATION_TIME},
                    code='invalid_minimum_duration'
                )

            if (cleaned_data['duration'].total_seconds() / 60) % settings.FABCAL_RESERVATION_INCREMENT_TIME != 0:
                raise ValidationError(
                    _("Please reserve in %(time)s minute increments!"),
                    params={'time': settings.FABCAL_MINIMUM_RESERVATION_TIME},
                    code='invalid_duration'
                )

        return cleaned_data

    def create_email_content(self):
        """
        Create email content for the machine reservation confirmation email.
        This function does not take any parameters and returns a dictionary containing the email content.
        """
        context = {
            'machine': self.instance.machine.title,
            'duration': self.instance.get_duration,
            'start_date': self.instance.formatted_start_date,
            'start_time': self.instance.formatted_start_time,
            'end_time': self.instance.formatted_end_time,
            'profile_url': reverse('accounts:profile'),
            'mail_url': 'mailto://' + os.environ.get('EMAIL_HOST_USER'),
        }

        email_body = mark_safe(_('You successfully booked the machine %(machine)s during %(duration)s minutes on %(start_date)s from %(start_time)s to %(end_time)s') % context)

        cancellation_policy = mark_safe(_('Please note that you may cancel this reservation up to 24 hours prior to the start of the slot without charge via your <a href="%(profile_url)s">account page on our website</a>. However, if you wish to cancel your reservation after this period, please <a href="%(mail_url)s">inform us by email</a>. In this case, we are sorry to inform you that we will be obliged to charge you for the machine hours, as the reserved machine could not be used by another person at that time. Thank you for your understanding.') % context)

        html_message = render_to_string('fabcal/email/confirmation.html', {'email_body': email_body, 'cancellation_policy': cancellation_policy})

        subject = _('Confirmation of your machine reservation')

        # Define email content as a dictionary
        email_content = {
            'from_email': None,
            'subject': subject,
            'message': subject,  # Using the subject as the plain text message
            'recipient_list': [self.user.email],
            'html_message': html_message,
        }

        return email_content

    def save(self):
        """
        A method to save the changes made to the instance, including creating new slots, updating existing slots, and sending mail.
        """
        initial_machine_slot = MachineSlot.objects.get(pk=self.instance.pk)
        start = self.cleaned_data['start']
        end = self.cleaned_data['end']

        # check if a machine slot is created or updated
        if initial_machine_slot.user is None:
            # create case

            # update slot for user
            self.instance.user = self.user

            if initial_machine_slot.start < start:
                # create a new empty slot at the begining
                new_slot = deepcopy(initial_machine_slot)
                new_slot.id = None
                new_slot.end = start
                new_slot.save()
            
            if initial_machine_slot.end > end:
                # create a new empty slot at the end
                new_slot = deepcopy(initial_machine_slot)
                new_slot.id = None
                new_slot.start = end
                new_slot.save()

        else:
            # update case

            if initial_machine_slot.start > start:
                previous_slot = initial_machine_slot.previous_slots(start).first()
                if previous_slot.start == start:
                    previous_slot.delete()
                else:
                    previous_slot.end = start
                    previous_slot.save()

            if initial_machine_slot.end < end:
                next_slot = initial_machine_slot.next_slots(end).first()
                if next_slot.end == end:
                    next_slot.delete()
                else:
                    next_slot.start = end
                    next_slot.save()

            if initial_machine_slot.start < start:
                previous_slot = initial_machine_slot.previous_slots(initial_machine_slot.start).first()
                previous_slot.end = start
                previous_slot.save()

            if initial_machine_slot.end > end:
                next_slot = initial_machine_slot.next_slots(initial_machine_slot.end).first()
                next_slot.start = end
                next_slot.save()

        if self.instance.machine.category.name == '3D':
            for slot in MachineSlot.objects.filter(
                start__gt=self.cleaned_data['start'], 
                end__gt=self.cleaned_data['end'],
                machine=self.instance.machine).all():
                    # create a new empty slot at the end
                    slot.start = self.cleaned_data['end']
                    slot.save()

            for slot in MachineSlot.objects.filter(
                start__gt=self.cleaned_data['start'],
                end__lt=self.cleaned_data['end'],
                machine=self.instance.machine).all():
                # delete slot
                slot.delete()

        self.instance.start = start
        self.instance.end = end
        self.instance.save()
        
        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)
        
        return self.instance

class TrainingSlotForm(SlotLinkedToOpeningForm):
    training = forms.ModelChoiceField(
        queryset= Training.objects.filter(is_active=True),
        label=_('Training'),
        empty_label=_('Select a training'),
        error_messages={'required': _('Please select a training.')}
        )

    class Meta:
        model = TrainingSlot
        fields = ('training', 'registration_limit', 'opening', 'machines', 'date', 'start_time', 'end_time', 'comment')

    def create_email_content(self):

        recipient_list = [
            training_notification.profile.user.email
            for training_notification in TrainingNotification.objects.filter(
                training=self.cleaned_data['training']
            )
        ]

        email_content = {
            'from_email': None,
            'recipient_list': recipient_list,
        }

        return email_content

class TrainingSlotCreateForm(TrainingSlotForm):
    def create_email_content(self):
        email_content = super().create_email_content()
        context = {'training_slot': self.instance}
        email_content['html_message'] = render_to_string('fabcal/email/training_create_alert.html', context)
        email_content['subject'] = _('A new training was planned')
        email_content['message'] = _("A new training was planned")

        return email_content
    
    def save(self):
        self.instance = super().save(OpeningSlotCreateForm)
        
        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)
        
        return self.instance

class TrainingSlotUpdateForm(TrainingSlotForm):
    def create_email_content(self):
        email_content = super().create_email_content()
        context = {'training_slot': self.instance}
        email_content['html_message'] = render_to_string('fabcal/email/training_update_alert.html', context)
        email_content['subject'] = _('A training was updated')
        email_content['message'] = _("A training was updated"),

        return email_content

    def save(self):
        self.instance = super().save(OpeningSlotUpdateForm, initial=self.initial)

        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)

        return self.instance

class TrainingSlotRegistrationForm(UserForm):

    class Meta:
        model = TrainingSlot
        fields = ('registrations',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['registrations'].required = False

    def create_email_content(self):
        email_content = {
            'from_email': None,
            'recipient_list': [self.user.email],
        }

        return email_content

class TrainingSlotRegistrationCreateForm(TrainingSlotRegistrationForm):
    
    def create_email_content(self):
        email_content = super().create_email_content()
        context = {'training_slot': self.instance}
        email_content['html_message'] = render_to_string('fabcal/email/trainingslot_registration_confirm.html', context)
        email_content['subject'] = _('Training registration confirmation')
        email_content['message'] = _("Training registration confirmation")

        return email_content
    
    def save(self):
        self.instance.registrations.add(self.user)

        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)
        
        return self.instance

class TrainingSlotRegistrationDeleteForm(TrainingSlotRegistrationForm):

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.user not in self.object.registrations.all():
            return HttpResponseForbidden("You are not allowed to access this page.")
        return super().dispatch(request, *args, **kwargs)

    def is_valid(self):
        if self.user not in self.instance.registrations.all():
            raise forms.ValidationError(_("You are not registered for this training slot."))
            return False
        return super().is_valid()
    
    def create_email_content(self):
        email_content = super().create_email_content()
        context = {'training_slot': self.instance}
        email_content['html_message'] = render_to_string('fabcal/email/trainingslot_unregistration_confirm.html', context)
        email_content['subject'] = _('Training unregistration confirmation')
        email_content['message'] = _("Training unregistration confirmation")

        return email_content
    
    def save(self):
        self.instance.registrations.remove(self.user)

        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)
        
        return self.instance

class EventSlotForm(SlotLinkedToOpeningForm):
    event = forms.ModelChoiceField(
        queryset= Event.objects.filter(is_active=True),
        label=_('Event'),
        empty_label=_('Select an event'),
        error_messages={'required': _('Please select an event.')}, 
        )
    price = forms.CharField(label=_('Price'), widget=forms.Textarea(attrs={'class':'form-control', 'rows':4}))
    has_registration = forms.BooleanField(required=False, label=_('On registration'))
    registration_limit = forms.IntegerField(required=False, label=_('Registration limit'), help_text=_('leave blank if no limit'))

    class Meta: 
        model = EventSlot
        fields = ('event', 'date', 'start_time', 'end_time', 'price', 'has_registration', 'registration_limit', 'opening', 'machines', 'comment')

class EventSlotCreateForm(EventSlotForm):
    def save(self):
        self.instance = super().save(OpeningSlotCreateForm)
        return self.instance

class EventSlotUpdateForm(EventSlotForm):
    def save(self):
        self.instance = super().save(OpeningSlotUpdateForm, initial=self.initial)
        return self.instance

class EventForm(AbstractSlotForm):
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
            'start': self.cleaned_data['start'].strftime("%Y%m%dT%H%M%SZ"),
            'end': self.cleaned_data['end'].strftime("%Y%m%dT%H%M%SZ")
        }
        
        messages.success(
            view.request,
            mark_safe(_('Your event has been successfully %(crud_state)s on %(start_date)s from %(start_time)s to %(end_time)s</br><a href="/fabcal/download-ics-file/%(event_title)s/%(start)s/%(end)s"><i class="bi bi-file-earmark-arrow-down-fill"></i> Add to my calendar</a>')
            % context))

class RegisterEventForm(forms.Form):
    pass

class MachineReservationForm(AbstractSlotForm):

    def __init__(self, machine_slot, next_machine_slot, previous_machine_slot, *args, **kwargs):
        super(MachineReservationForm, self).__init__(*args, **kwargs)
        self.machine_slot = machine_slot
        self.next_machine_slot = next_machine_slot
        self.previous_machine_slot = previous_machine_slot

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
        
        return self.cleaned_data['end']
