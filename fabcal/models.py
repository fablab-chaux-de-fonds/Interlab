from django.conf import settings
from django.db import models
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
    class Meta:
        verbose_name = _("Opening Slot")
        verbose_name_plural = _("Opening Slots")

    def __str__(self):
        return self.opening.title
