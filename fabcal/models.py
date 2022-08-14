import datetime

from django.conf import settings
from django.db import models
from cms.models import CMSPlugin
from django.utils.translation import gettext_lazy as _

from openings.models import Opening, Event

# Create your models here.
class AbstractSlot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    comment = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        abstract = True

class OpeningSlot(AbstractSlot):
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE)
    class Meta:
        verbose_name = _("Opening Slot")
        verbose_name_plural = _("Opening Slots")

    def clean(self):
        from django.core.exceptions import ValidationError
        """
        Ensure that the end datetime of the slot is after the start datetime
        """
        print(self.__dict__)
        if self.end <= self.start:
            raise ValidationError(
                _("End datetime sould be after start datetime")
            )

    def __str__(self):
        return self.opening.title

    def get_day_of_the_week(self):
        return self.start.strftime("%A")


class WeeklyPluginModel(CMSPlugin):
    pass

class CalendarOpeningsPluginModel(CMSPlugin):
    pass

class EventSlot(AbstractSlot):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    has_registration = models.BooleanField()
    registrations = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='event_registration_users', blank=True, null=True)
    registration_limit = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    price = models.TextField(max_length=255)
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE, blank=True, null=True)
    
    # machines = models.ManyToManyField() #issue41

    class Meta:
        verbose_name = _("Event Slot")
        verbose_name_plural = _("Event Slots")

    @property
    def is_single_day(self):
        return self.start.date() == self.end.date()
    
    @property
    def available_registration (self):
        "Check if there is still place for the event"
        if self.registration_limit:
            return self.registration_limit - self.registrations.count()
        else:
            return None
    @property
    def is_registration_open(self):
        "Check registration deadline (24h) "
        return datetime.datetime.now()-datetime.timedelta(hours=24) < self.start

class EventsListPluginModel(CMSPlugin):
    pass