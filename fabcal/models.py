import datetime

from babel.dates import format_datetime
from cms.models import CMSPlugin

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from openings.models import Opening, Event
from machines.models import Training, Machine

from .validators import validate_conflicting_openings
from .validators import validate_time_range
from .validators import validate_update_opening_slot_on_machine_slot
from .validators import validate_delete_opening_slot

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
    registration_limit = models.IntegerField(blank=True, null=True)

    @property
    def available_registration(self):
        "Check if there is still place for the event/training"
        if self.registration_limit:
            return self.registration_limit - self.registrations.count()
        else:
            return None
    class Meta:
        abstract = True
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
    has_registration = models.BooleanField()
    registrations = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='event_registration_users', blank=True)
    is_active = models.BooleanField(default=True)
    price = models.TextField(max_length=255)
    opening_slot = models.ForeignKey(OpeningSlot, on_delete=models.CASCADE, blank=True, null=True)
    
    # machines = models.ManyToManyField() #issue41

    class Meta:
        verbose_name = _("Event Slot")
        verbose_name_plural = _("Event Slots")

class TrainingSlot(AbstractSlot, AbstractRegistration):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    opening_slot = models.ForeignKey(OpeningSlot, on_delete=models.CASCADE, blank=True, null=True)
    registrations = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='training_registration_users', blank=True, null=True)

    class Meta:
        verbose_name = _("Training Slot")
        verbose_name_plural = _("Training Slots")

class MachineSlot(AbstractSlot):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, blank=True, null=True)
    opening_slot = models.ForeignKey(OpeningSlot, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = _("Machine Slot")
        verbose_name_plural = _("Machine Slots")

    @property
    def get_next_slot(self):
        return MachineSlot.objects.filter(
            Q(start__gt=self.start) &
            Q(machine=self.machine, user__isnull=False)
        ).order_by('start').first()

    @property
    def get_previous_slot(self):
        return MachineSlot.objects.filter(
            Q(start__lt=self.start) &
            Q(machine=self.machine, user__isnull=False)
        ).order_by('start').last()

    @property
    def get_next_free_slot(self):
        return MachineSlot.objects.filter(
            Q(start__gt=self.start) &
            Q(machine=self.machine, user__isnull=True)
        ).order_by('start').first()

    @property
    def get_previous_free_slot(self):
        return MachineSlot.objects.filter(
            Q(start__lt=self.start) &
            Q(machine=self.machine, user__isnull=True)
        ).order_by('start').last()


class EventsListPluginModel(CMSPlugin):
    pass