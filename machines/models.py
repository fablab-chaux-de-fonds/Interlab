import datetime

from django.db import models
from django.utils.translation import ugettext as _
from djangocms_text_ckeditor.fields import HTMLField
from cms.models import CMSPlugin

from accounts.models import Profile
from openings.models import AbstractOpening
from url_or_relative_url_field.fields import URLOrRelativeURLField

class ItemForRent(AbstractOpening):
    full_price = models.DecimalField(verbose_name=_('Price'),max_digits=6,decimal_places=2, null=True, blank=False)
    photo = models.ImageField(upload_to='img', verbose_name=_('Photo'))
    header = HTMLField(verbose_name=_('Header'),blank=True,configuration='CKEDITOR_SETTINGS')

    @property
    def faq_list(self):
        return self.faq_set.all()

class AbstractMachinesFilter(models.Model):
    name = models.CharField(max_length=255)
    sort = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.name
    class Meta:
        abstract = True


class MachineCategory(AbstractMachinesFilter):
    """For Training validation"""
    
    class Meta:
        verbose_name = _("Machine Category")
        verbose_name_plural = _("Machine Categories")

class Training(ItemForRent):
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
    sort = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return _('Training') + ' :' +self.title

    @property
    def outcome_list(self):
        return self.outcomelistitem_set.all()

    @property 
    def machines_list(self):
        """Query set for Machine with same category"""
        return Machine.objects.filter(category=self.machine_category)

    class Meta:
        verbose_name = _("Training")
        verbose_name_plural = _("Trainings")

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
    icon = models.ImageField(upload_to='icons', verbose_name=_('Icon'), blank=True, null=True)
    bootstrap_icon = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.CharField(max_length=255, verbose_name=_('Description'), blank=True)
    link = URLOrRelativeURLField(verbose_name=_('Link'), blank=True)
    link_text = models.CharField(max_length=255, verbose_name=_('Link text'), blank=True)

    def __str__(self):
        return self.title + " - " + self.description

    class Meta:
        verbose_name = _("Card")
        verbose_name_plural = _("Cards")

class AbstractCardSorting(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    sort = models.PositiveSmallIntegerField(default=1)
    class Meta:
        abstract = True

class ToolTraining(AbstractCardSorting):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Training tool")
        verbose_name_plural = _("Training tools")

class Faq(models.Model):
    about = models.ForeignKey(ItemForRent, on_delete=models.CASCADE)
    question = models.CharField(max_length=255, verbose_name=_('Question'))
    answer = HTMLField(verbose_name=_('Answer'),configuration='CKEDITOR_SETTINGS')

    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")

class MachineGroup(AbstractMachinesFilter):
    """For splitting machine in all machines view"""
    
    class Meta:
        verbose_name = _("Machine group")
        verbose_name_plural = _("Machine groups")

class Material(AbstractMachinesFilter):
    
    class Meta:
        verbose_name = _("Material")
        verbose_name_plural = _("Materials")

class Workshop(AbstractMachinesFilter):
    class Meta:
        verbose_name = _("Workshop")
        verbose_name_plural = _("Workshops")

class Machine(ItemForRent):

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
    category = models.ForeignKey(MachineCategory,null=True,on_delete=models.SET_NULL)
    material = models.ManyToManyField(Material, blank=True)
    workshop = models.ManyToManyField(Workshop, blank=True)
    reservable = models.BooleanField(default=True)
    premium_price = models.DecimalField(verbose_name=_('Premium Price'),max_digits=6,decimal_places=2, null=True, blank=False)

    def __str__(self):
        return _('Machine') + ': ' + self.title

    @property
    def highlights(self):
        return self.highlightmachine_set.all().order_by('sort')

    @property
    def materials(self):
        return self.material.all()

    @property
    def workshops(self):
        return self.workshop.all()

    @property
    def tools(self):
        return self.toolmachine_set.all().order_by('sort')

    @property
    def specifications(self):
        return self.specification_set.all().order_by('sort')

    @property
    def next_slots(self):
        return self.machineslot_set.filter(end__gt=datetime.datetime.now())

    @property
    def trained_profile_list(self):
        trainings = self.category.training_set.all()
        profile = []
        for training in trainings:
            profile.extend(training.trainingvalidation_set.values_list('profile', flat = True))
        return profile
    class Meta:
        verbose_name = _("Machine")
        verbose_name_plural = _("Machines")

class ToolMachine(AbstractCardSorting):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Machine tool")
        verbose_name_plural = _("Machine tools")

class HighlightMachine(AbstractCardSorting):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Machine highlight")
        verbose_name_plural = _("Machine highlights")

class Specification(models.Model):
    key = models.CharField(max_length=255)
    value = HTMLField(blank=True,configuration='CKEDITOR_SETTINGS')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    sort = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = _("Specification")
        verbose_name_plural = _("Specifications")

class TrainingsListPluginModel(CMSPlugin):
    pass

class MachinesListPluginModel(CMSPlugin):
    pass