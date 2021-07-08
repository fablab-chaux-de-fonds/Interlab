from django.db import models
from django.contrib.auth.models import User

class SubscriptionCategory(models.Model):
    title = models.CharField(max_length=255)
    price = models.FloatField()
    access_number = models.PositiveSmallIntegerField()

class Subscription(models.Model):
    expiration = models.DateField()
    category = models.ForeignKey(SubscriptionCategory, on_delete=models.CASCADE)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    newsletter = models.BooleanField()
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)


