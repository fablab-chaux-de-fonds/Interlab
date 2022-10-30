from django.db import models
from django.utils.translation import ugettext as _
from djangocms_text_ckeditor.fields import HTMLField
from cms.models import CMSPlugin

from accounts.models import Profile
from openings.models import AbstractOpening

class ItemForRent(models.Model):
    full_price = models.DecimalField(verbose_name=_('Price'),max_digits=6,decimal_places=2)

    def __str__(self):
        return self.title

class AbstractMachinesFilter(models.Model):
    name = models.CharField(max_length=255)
    sort = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.name
    class Meta:
        abstract = True


class MachineCategory(AbstractMachinesFilter):
    """For Training validation"""
    pass

class Training(ItemForRent, AbstractOpening):
    BEGINNER = 'BEG'
    INTERMEDIATE = 'INT'
    ADVANCED = 'ADV'

    LEVEL_CHOICES = [
        (BEGINNER, _('Beginner')),
        (INTERMEDIATE, _('Intermediate')),
        (ADVANCED, _('Advanced')),
    ]

    machine_category = models.ForeignKey(MachineCategory, on_delete=models.CASCADE, verbose_name=_('Machine category'))
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, verbose_name=_('Level'))
    duration = models.DurationField(verbose_name=_('Duration'), help_text=_('Use the format HH:MM:SS')) # TODO essayer de trouver un truc plus pratique pour dire la durée
    header = HTMLField(verbose_name=_('Header'),blank=True,configuration='CKEDITOR_SETTINGS')
    sort = models.PositiveSmallIntegerField(default=1)
    photo = models.ImageField(upload_to='trainings', verbose_name=_('Photo'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    @property
    def faq_list(self):
        return self.faq_set.all()

    @property
    def outcome_list(self):
        return self.outcomelistitem_set.all()

    @property 
    def machines_list(self):
        """Query set for Machine with same category"""
        return Machine.objects.filter(category=self.machine_category)

class AbstractTrainingProfile(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
class TrainingNotification(AbstractTrainingProfile):
    pass
class TrainingValidation(AbstractTrainingProfile):
    pass

class Card(models.Model):
    icon = models.ImageField(upload_to='icons', verbose_name=_('Icon'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.CharField(max_length=255, verbose_name=_('Description'), blank=True)
    link = models.URLField(verbose_name=_('Link'))
    link_text = models.CharField(max_length=255, verbose_name=_('Link text'))

    def __str__(self):
        return self.title + " - " + self.description

class AbstractCardSorting(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    sort = models.PositiveSmallIntegerField(default=1)
    class Meta:
        abstract = True

class ToolTraining(AbstractCardSorting):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)

class Faq(models.Model):
    about = models.ForeignKey(ItemForRent, on_delete=models.CASCADE)
    question = models.CharField(max_length=255, verbose_name=_('Question'))
    answer = HTMLField(verbose_name=_('Answer'),configuration='CKEDITOR_SETTINGS')

class MachineGroup(AbstractMachinesFilter):
    """For splitting machine in all machines view"""
    pass

class Material(AbstractMachinesFilter):
    pass

class Workshop(AbstractMachinesFilter):
    pass

class Machine(ItemForRent, AbstractOpening):

    STATUS_CHOICES = [
        ('hidden', 'Hidden'),
        ('available', 'Available'),
        ('maintenance', 'Maintenance')
    ]

    status = models.CharField(
        max_length=255,
        choices=STATUS_CHOICES,
        default='available'
    )

    group = models.ForeignKey(MachineGroup,null=True,on_delete=models.SET_NULL) 
    category = models.ForeignKey(MachineCategory, on_delete=models.CASCADE)
    material = models.ManyToManyField(Material, blank=True)
    workshop = models.ManyToManyField(Workshop, blank=True)
    reservable = models.BooleanField(default=True)
    spec = HTMLField(verbose_name=_('Specifications'),blank=True,configuration='CKEDITOR_SETTINGS')
    premium_price = models.DecimalField(verbose_name=_('Premium Price'),max_digits=6,decimal_places=2)
    photo = models.ImageField(upload_to='machines')

class ToolMachine(AbstractCardSorting):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

class HighlightMachine(AbstractCardSorting):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

class TrainingsListPluginModel(CMSPlugin):
    pass

class MachinesListPluginModel(CMSPlugin):
    pass