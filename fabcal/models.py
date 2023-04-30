import datetime

from cms.models import CMSPlugin

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from openings.models import Opening, Event
from machines.models import Training, Machine

# Create your models here.
class AbstractSlot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    comment = models.CharField(max_length=255, blank=True, null=True)
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

class EventsListPluginModel(CMSPlugin):
    pass