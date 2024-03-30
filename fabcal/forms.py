import os
import datetime
from copy import deepcopy
import dateparser

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

from machines.models import Training, TrainingNotification, Machine
from openings.models import Opening, Event

from .models import OpeningSlot, EventSlot, TrainingSlot, MachineSlot
from .custom_fields import CustomDateField
from .validators import validate_delete_machine_slot

class UserForm(ModelForm):
    def __init__(self, user=None,  *args, **kwargs):
        """
        Initialize the UserForm with optional user parameter.

        Parameters:
            user (optional): A user object.

        Returns:
            None
        """
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user

class SlotForm(UserForm):
    date = CustomDateField(required=False)
    start_time = forms.TimeField()
    end_time = forms.TimeField()
    comment = forms.CharField(label=_('Comment'),  required=False)

    def clean(self):
        """
        Clean the form data.

        This function combines the date, start_time, and end_time form fields
        with the instance start and end fields, and updates the instance
        before the clean in the model.

        Returns:
            cleaned_data (dict): The cleaned form data.
        """
        # Call the parent's clean method
        cleaned_data = super(SlotForm, self).clean()
        
        # Get the date, start_time, and end_time form fields or use the
        # instance start and end fields.
        date = cleaned_data.get('date') or self.instance.start.date()
        start_time = cleaned_data.get('start_time') or self.instance.start.time()
        end_time = cleaned_data.get('end_time') or self.instance.end.time()

        # Combine the date, start_time, and end_time with the instance start
        # and end fields to set the start and end fields of the instance.
        self.cleaned_data['start'] = datetime.datetime.combine(date, start_time)
        self.cleaned_data['end'] = datetime.datetime.combine(date, end_time)

        # Update the instance before clean in the model.
        self.instance.start = self.cleaned_data['start']
        self.instance.end = self.cleaned_data['end']

        return cleaned_data

class RegistrationForm(UserForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['registrations'].required = False

    def save(self):

        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)

        return self.instance

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
            initial (dict): The initial data for the opening slot form.

        Returns:
            instance: The created instance.
        """
        # Save the instance of the superclass
        self.instance = super().save()

        # Get the opening data from the cleaned data
        opening_data = self.cleaned_data.get('opening')

        # If opening data is present
        if opening_data:
            # Prepare the form data for the opening slot form
            form_data = {
                'opening': opening_data,
                'machines': self.cleaned_data.get('machines'),
                'date': self.cleaned_data.get('date'),
                'start_time': self.cleaned_data.get('start_time'),
                'end_time': self.cleaned_data.get('end_time'),
                'comment': self.cleaned_data.get('comment')
            }

            # Create the opening slot form using the form class and data
            form = opening_slot_form_class(
                data=form_data,
                initial=initial,
                instance=self.instance.opening_slot,
            )

            # Validate the form data
            form.is_valid()

            # Save the opening slot form
            opening_slot = form.save()
        
            # Update the instance with the opening slot
            self.instance.opening_slot = opening_slot
        
        # Save the updated instance
        self.instance.save()

        return self.instance

class OpeningSlotCreateForm(OpeningSlotForm):

    def save(self):
        """
        Save the instance of the OpeningSlotCreateForm.

        This function creates a new MachineSlot for each machine in
        the cleaned_data['machines'] and saves it to the database.

        Returns:
            instance (OpeningSlot): The saved instance of OpeningSlot.
        """
        self.instance = super().save()
        self.instance.save()

        # Create a MachineSlot for each machine in cleaned_data['machines']
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
        """
        Clean the form data by removing MachineSlots associated with machines
        that are no longer selected.

        Returns:
            cleaned_data (dict): The cleaned form data.
        """
        # Get the set of machine primary keys to remove
        machines_to_remove = set(self.initial.get('machines', [])) - set(self.cleaned_data['machines'].values_list('pk', flat=True))

        # Remove MachineSlots associated with machines to remove
        for pk in machines_to_remove:
            machine_slot = MachineSlot.objects.get(opening_slot=self.instance, machine=pk)
            validate_delete_machine_slot(machine_slot)

        return super().clean()

    def save(self):
        """
        A method to save the instance and perform operations to remove, update, or create machine slots.
        """
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
        """
        Cleans the start time of the form data.

        Returns:
            datetime: The cleaned start time.

        Raises:
            ValidationError: If the start time is earlier than the opening slot start time.
        """
        start_time = self.cleaned_data.get('start_time')

        if self.cleaned_data['start_time'] < self.instance.opening_slot.start.time():
            raise ValidationError(
                    _("You cannot start earlier than %(start_time)s"),
                    params={'start_time': self.instance.start.time().strftime('%H:%M')},
                    code='invalid_start_time'
                )
                
        return start_time

    def clean_end_time(self):
        """
        Cleans and validates the end time of a form.

        Returns:
            The cleaned and validated end time.
        
        Raises:
            ValidationError: If the end time is later than the opening slot end time.
        """
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
                if previous_slot:
                    previous_slot.end = start
                    previous_slot.save()
                else:
                    new_slot = deepcopy(initial_machine_slot)
                    new_slot.id = None
                    new_slot.end = start
                    new_slot.user= None
                    new_slot.save()

            if initial_machine_slot.end > end:
                next_slot = initial_machine_slot.next_slots(initial_machine_slot.end).first()
                if next_slot:
                    next_slot.start = end
                    next_slot.save()
                else: 
                    new_slot = deepcopy(initial_machine_slot)
                    new_slot.id = None
                    new_slot.start = end
                    new_slot.user= None
                    new_slot.save()

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
        """
        Saves the instance of the form and sends an email with the created email content.

        Returns:
            The saved instance of the form.
        """
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
        """
        Save the instance using the OpeningSlotUpdateForm, initialize email content, and send mail.
        Returns the saved instance.
        """
        self.instance = super().save(OpeningSlotUpdateForm, initial=self.initial)

        # send mail
        email_content = self.create_email_content()
        send_mail(**email_content)

        return self.instance

class TrainingSlotRegistrationForm(RegistrationForm):

    class Meta:
        model = TrainingSlot
        fields = ('registrations',)

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
        return super(TrainingSlotRegistrationCreateForm, self).save()

class TrainingSlotRegistrationDeleteForm(TrainingSlotRegistrationForm):

    def is_valid(self):
        """
        Check if the form is valid.

        This method checks if the user is registered for the training slot associated with the form instance. If the user is not registered, a validation error is raised. Otherwise, the parent class's `is_valid` method is called to perform further validation.

        Returns:
            bool: True if the form is valid, False otherwise.

        Raises:
            forms.ValidationError: If the user is not registered for the training slot.
        """
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
        return super(TrainingSlotRegistrationDeleteForm, self).save()

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

class EventSlotRegistraionForm(RegistrationForm):

    class Meta:
        model = EventSlot
        fields = ('registrations',)

    def create_email_content(self):
        email_content = {
            'from_email': None,
            'recipient_list': [self.user.email],
        }

        return email_content

class EventSlotRegistrationCreateForm(EventSlotRegistraionForm):
    def create_email_content(self):
        email_content = super().create_email_content()
        context = {'event_slot': self.instance}
        email_content['html_message'] = render_to_string('fabcal/email/eventslot_registration_confirm.html', context)
        email_content['subject'] = _('Event registration confirmation')
        email_content['message'] = _("Event registration confirmation")

        return email_content
    
    def save(self):
        self.instance.registrations.add(self.user)
        return super(EventSlotRegistrationCreateForm, self).save()

class EventSlotRegistrationDeleteForm(EventSlotRegistraionForm):

    def is_valid(self):
        if self.user not in self.instance.registrations.all():
            raise forms.ValidationError(_("You are not registered for this event slot."))
            return False
        return super().is_valid()
    
    def create_email_content(self):
        email_content = super().create_email_content()
        context = {'event_slot': self.instance}
        email_content['html_message'] = render_to_string('fabcal/email/eventslot_unregistration_confirm.html', context)
        email_content['subject'] = _('Event unregistration confirmation')
        email_content['message'] = _("Event unregistration confirmation")

        return email_content
    
    def save(self):
        self.instance.registrations.remove(self.user)
        return super(EventSlotRegistrationDeleteForm, self).save()

