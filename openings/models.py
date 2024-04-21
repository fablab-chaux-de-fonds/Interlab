from django.db import models
from django.utils.translation import gettext_lazy as _
from djangocms_text_ckeditor.fields import HTMLField

from colorfield.fields import ColorField

class AbstractOpening(models.Model):
    COLOR_PALETTE = [
        ("#0b1783", "blue", ),
        ("#ddf9ff", "blue-light", ),
        ("#e3005c", "red", ),
        ("#ffe8e0", "red-light", ),
        ("#00a59f", "green", ),
        ("#e4f2e5", "green-light", ),
    ]
    title = models.CharField(max_length=255)
    desc = HTMLField(verbose_name=_('Description'),blank=True,configuration='CKEDITOR_SETTINGS')
    color = ColorField(default='#ffffff', samples=COLOR_PALETTE)
    background_color = ColorField(default='#0b1783', samples=COLOR_PALETTE)
    photo = models.ImageField(upload_to='img', verbose_name=_('Photo'), default='/img/opening.jpg')

    class Meta:
        abstract = True
    
    def __str__(self):
        return self.title
    
class Opening(AbstractOpening):
    desc = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    is_open_to_reservation = models.BooleanField()
    is_open_to_questions = models.BooleanField()
    is_reservation_mandatory = models.BooleanField()
    is_public = models.BooleanField()

    class Meta:
        verbose_name = _("Opening")
        verbose_name_plural = _("Openings")

class Event(AbstractOpening):
    lead = models.TextField(blank=True, null=True)
    is_on_site = models.BooleanField()
    location = models.CharField(max_length=255, default='Fablab')
    is_active = models.BooleanField()

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")   