from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

import machines

class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)

    def __str__(self):
        return self.first_name + ' ' +  self.last_name + ' <' + self.email + '>'
class SubscriptionCategory(models.Model):
    title = models.CharField(max_length=255)
    price = models.IntegerField() # Swiss Franc
    default_access_number = models.PositiveSmallIntegerField(default=1)
    duration = models.PositiveSmallIntegerField(default=365) # in days
    star_flag = models.BooleanField()
    sort = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = "Subscription Categories"

    def get_display_price(self):
            return "{0:.2f}".format(self.price / 100)

class Subscription(models.Model):
    start = models.DateField()
    end = models.DateField()
    subscription_category = models.ForeignKey(SubscriptionCategory, on_delete=models.CASCADE, null=True)
    access_number = models.PositiveSmallIntegerField()

    def __str__(self):
        if self.subscription_category==None:
            return f"No subscription_category, {self.access_number}, {self.start}, {self.end}"
        return f"{self.subscription_category.title}, {self.access_number}, {self.start}, {self.end}"

class Profile(models.Model):
    PUBLIC_CONTACT_PLATEFORM_CHOICES =[
        ('discord', 'Discord'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('linkedin', 'Linkedin'),
        ('envelope', 'e-mail'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name=_('Phone number'))
    public_contact_plateform = models.CharField(max_length=255, blank=True, null=True, choices=PUBLIC_CONTACT_PLATEFORM_CHOICES, verbose_name=_('Plublic chanel'))
    public_contact = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Public contact'))

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}, ({self.user.username})"

    @property 
    def get_training_validations(self):
        return self.trainingvalidation_set.all()

    @property 
    def is_subscription_valid(self):
        if self.subscription:
            return date.today() >= self.subscription.start and date.today() <= self.subscription.end
        else:
            return False

class SuperUserStatus(models.Model):
    status = models.CharField(max_length=255)

    def __str__(self):
        return self.status

class SuperUserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to="profile")
    about_me = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("About me"))
    status = models.ManyToManyField(SuperUserStatus, verbose_name=_("Status"), blank=True, null=True)
    trainer = models.ManyToManyField("machines.Training", verbose_name=_("Trainer"), blank=True, null=True)
    technique = models.ManyToManyField("machines.Workshop", verbose_name=_("Technique"), blank=True, null=True)
    software = models.ManyToManyField("machines.Software", verbose_name=_("Software"), blank=True, null=True)
    machine_category =  models.ManyToManyField("machines.MachineCategory", verbose_name=_("Machine category"), blank=True, null=True)

    def __str__(self):
        return str(self.user)

from cms.models import CMSPlugin
class SuperUserListPluginModel(CMSPlugin):
    pass