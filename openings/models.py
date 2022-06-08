from django.db import models
from django.utils.translation import gettext_lazy as _

from colorfield.fields import ColorField

# Create your models here.
class Opening(models.Model):
    COLOR_PALETTE = [
        ("#0b1783", "blue", ),
        ("#ddf9ff", "blue-light", ),
        ("#e3005c", "red", ),
        ("#ffe8e0", "red-light", ),
        ("#00a59f", "green", ),
        ("#e4f2e5", "green-light", ),
    ]

    title = models.CharField(max_length=255)
    desc = models.TextField()
    color = ColorField(samples=COLOR_PALETTE)
    background_color = ColorField(samples=COLOR_PALETTE)
    is_open_to_reservation = models.BooleanField()
    is_open_to_questions = models.BooleanField()
    is_reservation_mandatory = models.BooleanField()
    is_public = models.BooleanField()
    class Meta:
        verbose_name = _("Opening")
        verbose_name_plural = _("Openings")

    def __str__(self):
        return self.title
