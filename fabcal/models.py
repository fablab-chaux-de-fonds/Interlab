from django.conf import settings
from django.db import models
from cms.models import CMSPlugin
from django.utils.translation import gettext_lazy as _

from openings.models import Opening

# Create your models here.
class AbstractSlot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    class Meta:
        abstract = True

class OpeningSlot(AbstractSlot):
    opening = models.ForeignKey(Opening, on_delete=models.CASCADE)
    comment = models.CharField(max_length=255, blank=True, null=True)
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