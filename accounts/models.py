from django.db import models
from django.contrib.auth.models import User

class SubscriptionCategory(models.Model):
    title = models.CharField(max_length=255)
    price = models.FloatField()
    default_access_number = models.PositiveSmallIntegerField(default=1)
    duration = models.PositiveSmallIntegerField(default=360) # in days
    star_flag = models.BooleanField()
    sort = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = "Subscription Categories"

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}, ({self.user.username})"

