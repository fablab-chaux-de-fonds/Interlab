from django.db import models
from django.contrib.auth.models import User

class SubscriptionCategory(models.Model):
    title = models.CharField(max_length=255)
    price = models.FloatField()
    access_number = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.title}"

class Subscription(models.Model):
    expiration = models.DateField()
    category = models.ForeignKey(SubscriptionCategory, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.title}, {self.expiration}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    newsletter = models.BooleanField()
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, blank=True, null=True)

