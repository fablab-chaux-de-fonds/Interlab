from django.db import models
from django.utils.translation import ugettext as _


class ItemForRent(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    price = models.FloatField(verbose_name=_('Price'))


class MachineCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

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
    duration = models.DurationField(verbose_name=_('Duration'))
    # header = ??? # like html header?
    # support = ??? # isn't it linked to machine instead?
    # sort = ??? # is it to enforce an order?
    photo = models.ImageField(upload_to='trainings', verbose_name=_('Photo'))

    def __str__(self):
        return self.title


class OutcomeListItem(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    description = models.TextField(verbose_name=_('Description'))


class DIYListItem(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    name = models.CharField(max_length=255, blank=True, verbose_name=_('Name'))
    url = models.URLField(blank=True)


class Faq(models.Model):
    about = models.ForeignKey(ItemForRent, on_delete=models.CASCADE)
    question = models.CharField(max_length=255, verbose_name=_('Question'))
    answer = models.TextField(verbose_name=_('Answer'))


class Machine(ItemForRent):
    category = models.ForeignKey(MachineCategory, on_delete=models.CASCADE)  # TODO why exactly ??
    # status = ???
    # model = ??
    visible = models.BooleanField(default=True)
    reservable = models.BooleanField(default=True)  # isn't it linked to the status??
    # group = ???
    support = models.URLField()
    spec = models.TextField()  # TODO I think it could be more guided with categories etc
    # sort = ???
    subscriber_price = models.FloatField()  # TODO is it for trainings too?
    photo = models.ImageField(upload_to='machines')


class MachineTodoPoint(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    seen_in_training = models.BooleanField(default=False)
    sort = models.PositiveSmallIntegerField()
