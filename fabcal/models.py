import datetime

from babel.dates import format_datetime
from cms.models import CMSPlugin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from openings.models import Opening, Event
from machines.models import Training, Machine

from .validators import validate_conflicting_openings
from .validators import validate_time_range
from .validators import validate_update_opening_slot_on_machine_slot
from .validators import validate_delete_opening_slot
from .validators import url_or_email_validator

class AbstractSlot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    comment = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    class Meta:
        abstract = True

    @property
    def get_duration(self):
        return int((self.end-self.start).seconds / 60)

    @property
    def is_editable(self):
        if self.start-datetime.timedelta(days=1) > datetime.datetime.now():
            return True 
        else:
            return False

    @property
    def is_single_day(self):
        return self.start.date() == self.end.date()

    def get_formatted_datetime(self, datetime_value, time_format):
        return format_datetime(datetime_value, time_format, locale=settings.LANGUAGE_CODE)

    @property
    def formatted_start_date(self):
        return self.get_formatted_datetime(self.start, "EEEE d MMMM y")

    @property
    def formatted_start_time(self):
        return self.get_formatted_datetime(self.start, "H:mm")

    @property
    def formatted_end_date(self):
        return self.get_formatted_datetime(self.end, "EEEE d MMMM y")

    @property
    def formatted_end_time(self):
        return self.get_formatted_datetime(self.end, "H:mm")

class AbstractRegistration(models.Model):
    registration_limit = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def available_registration(self):
        "Check if there is still place for the event/training"
        return self.registration_limit - self.get_number_of_attendees

        
class OpeningSlot(AbstractSlot):
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE)
    class Meta:
        verbose_name = _("Opening Slot")
        verbose_name_plural = _("Opening Slots")

    def __str__(self):
        return str(self.pk) +' :' + self.opening.title

    def clean(self):
        validate_conflicting_openings(self.start, self.end, instance=self)
        validate_time_range(self.start, self.end)
        validate_update_opening_slot_on_machine_slot(self)

    def delete(self):
        validate_delete_opening_slot(self)
        return super(OpeningSlot, self).delete()

    @property
    def get_day_of_the_week(self):
        return self.start.strftime("%A")
    
    @property
    def get_machine_list(self):
        return [i.machine for i in self.machineslot_set.all()]
    
    @property
    def get_reservation_list(self):
        return self.machineslot_set.filter(user__isnull=False)

    @property
    def can_be_deleted(self):
        return not bool(self.machineslot_set.filter(user__isnull=False).exists())

class WeeklyPluginModel(CMSPlugin):
    pass

class CalendarOpeningsPluginModel(CMSPlugin):
    pass

class EventSlot(AbstractSlot, AbstractRegistration):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registration_required = models.BooleanField()
    registration_type = models.CharField(
        max_length=20,
        choices=[('onsite', 'On-site'), ('external', 'External')],
        blank=True,
        null=True, 
        help_text=_('Define whether event registration is done directly on the fablab site or on the external site')
    )
    external_registration_link = models.CharField(
        max_length=2048,
        blank=True,
        null=True,
        validators=[url_or_email_validator],
        help_text=_('Enter URL or email address')
    )
    is_active = models.BooleanField(default=True)
    price = models.TextField(max_length=255)
    opening_slot = models.ForeignKey(OpeningSlot, on_delete=models.CASCADE, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True, help_text=_("Additional information sent by e-mail upon registration"))

    class Meta:
        verbose_name = _("Event Slot")
        verbose_name_plural = _("Event Slots")
        
    def __str__(self):
        return f"{self.start} - {self.event.title}"

    def clean(self):
        # If registration is required, ensure registration type is specified
        if self.registration_required:
            if not self.registration_type:
                raise ValidationError(_('Registration type must be specified if registration is required.'))

            if self.registration_type == 'onsite' and (self.registration_limit is None or self.registration_limit < 0):
                raise ValidationError(_('Registration limit must be specified if registration type is on-site.'))
                
            if self.registration_type == 'external' and not self.external_registration_link:
                raise ValidationError(_('External registration link must be specified if registration type is external.'))

            #check if user already register to the event slot
            if True:
                pass

    def delete(self, *args, **kwargs):
        if self.registrations.all().exists():
            raise ValidationError(_("Cannot delete event slot with registrations."), code='event_slot_with_registrations')
        super().delete(*args, **kwargs)

    @property
    def get_reservation_list(self):
        # Fetch all registrations for this event slot, including the related user data
        registrations = RegistrationEventSlot.objects.filter(event_slot=self)
        
        # Prepare the list of users with the number of attendees included
        user_list = []
        for registration in registrations:
            user = registration.user
            user.number_of_attendees = registration.number_of_attendees
            user_list.append(user)
        
        return user_list

    @property
    def get_number_of_attendees(self):
        total_attendees = RegistrationEventSlot.objects.filter(event_slot=self).aggregate(total=Sum('number_of_attendees'))['total']
        return total_attendees if total_attendees is not None else 0
        
class RegistrationEventSlot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registration_users', blank=True)
    event_slot = models.ForeignKey(EventSlot, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    number_of_attendees = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.pk} - {self.user} registered {self.number_of_attendees} people for {self.event_slot} on {self.registration_date}"
    
    class Meta:
        verbose_name = _("Event slot Registration")
        verbose_name_plural = _("Event slot registrations")

class TrainingSlot(AbstractSlot, AbstractRegistration):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    opening_slot = models.ForeignKey(OpeningSlot, on_delete=models.CASCADE, blank=True, null=True)
    registrations = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='training_registration_users', blank=True)

    class Meta:
        verbose_name = _("Training Slot")
        verbose_name_plural = _("Training Slots")

    def delete(self, *args, **kwargs):
        if self.registrations.all().exists():
            raise ValidationError(_("Cannot delete Training Slot with registrations."), code='training_slot_with_registrations')
        super().delete(*args, **kwargs)
    
    @property
    def get_reservation_list(self):
        return self.registrations.all()

    @property
    def get_number_of_attendees(self):
        return self.registrations.all().count()

class MachineSlot(AbstractSlot):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, blank=True, null=True)
    opening_slot = models.ForeignKey(OpeningSlot, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = _("Machine Slot")
        verbose_name_plural = _("Machine Slots")

    def next_slots(self, until):
        """
        Retrieve the next available machine slot until the specified time.

        :param until: The end time until which the machine slots should be retrieved.
        :return: The first available machine slot that meets the specified conditions or None if no slot is available.
        """
        return MachineSlot.objects.filter(
            Q(end__gt=self.end) &
            Q(start__lte=until) &
            Q(machine=self.machine)
        ).order_by('end')

    def previous_slots(self, until):
        """
        Retrieve the previous available machine slot until the specified time.

        :param until: The start time until which the machine slots should be retrieved.
        :return: The last available machine slot that meets the specified conditions or None if no slot is available.
        """
        return MachineSlot.objects.filter(
            Q(start__lt=self.start) &
            Q(end__gte=until) &
            Q(machine=self.machine)
        ).order_by('-start')

class EventsListPluginModel(CMSPlugin):
    pass
