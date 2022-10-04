from django.db import models
from django.utils.translation import ugettext as _
from djangocms_text_ckeditor.fields import HTMLField

class ItemForRent(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = HTMLField(verbose_name=_('Description'),blank=True,configuration='CKEDITOR_SETTINGS')
    price = models.DecimalField(verbose_name=_('Price'),max_digits=6,decimal_places=2)

    def __str__(self):
        return self.title


class MachineCategory(models.Model):
    name = models.CharField(max_length=255)
    description = HTMLField(verbose_name=_('Description'),blank=True,configuration='CKEDITOR_SETTINGS')

    def __str__(self):
        return self.name


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
    header = HTMLField(verbose_name=_('Header'),blank=True,configuration='CKEDITOR_SETTINGS')
    support = HTMLField(verbose_name=_('Support'),blank=True,configuration='CKEDITOR_SETTINGS')
    sort = models.PositiveSmallIntegerField(default=1)
    photo = models.ImageField(upload_to='trainings', verbose_name=_('Photo'))

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


class OutcomeListItem(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    description = HTMLField(verbose_name=_('Description'),blank=True,configuration='CKEDITOR_SETTINGS')


class DIYListItem(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    name = models.CharField(max_length=255, blank=True, verbose_name=_('Name'))
    url = models.URLField(blank=True)


class Faq(models.Model):
    about = models.ForeignKey(ItemForRent, on_delete=models.CASCADE)
    question = models.CharField(max_length=255, verbose_name=_('Question'))
    answer = HTMLField(verbose_name=_('Answer'),configuration='CKEDITOR_SETTINGS')

class MachineGroup(models.Model):
    """For splitting machine in all machines view"""
    title = models.CharField(max_length=255)
    description = HTMLField(verbose_name=_('Specifications'),blank=True,configuration='CKEDITOR_SETTINGS')
    sort = models.PositiveSmallIntegerField(default=1)

class Machine(ItemForRent):
    category = models.ForeignKey(MachineCategory, on_delete=models.CASCADE)  # TODO why exactly ??
    # status = ???
    # model = ??
    visible = models.BooleanField(default=True)
    reservable = models.BooleanField(default=True)
    group = models.ForeignKey(MachineGroup,null=True,on_delete=models.SET_NULL) 
    support = models.URLField()
    spec = HTMLField(verbose_name=_('Specifications'),blank=True,configuration='CKEDITOR_SETTINGS')
    sort = models.PositiveSmallIntegerField(default=1)
    subscriber_price = models.DecimalField(verbose_name=_('Subscriber price'),max_digits=6,decimal_places=2)
    photo = models.ImageField(upload_to='machines')


class MachineTodoPoint(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    seen_in_training = models.BooleanField(default=False)
    sort = models.PositiveSmallIntegerField(default=1)

