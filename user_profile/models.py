from django.db import models
from django.contrib.auth.models import User

class SubscriptionCategory(models.Model):
    title = models.CharField(max_length=255)
    price = models.FloatField()
    access_number = models.PositiveSmallIntegerField()
    duration = models.PositiveSmallIntegerField(blank=True, null=True) # in days
    star_flag = models.BooleanField(blank=True, null=True)
    sort = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name_plural = "Subscription Categories"

class Subscription(models.Model):
    start = models.DateField()
    end = models.DateField()
    category = models.ForeignKey(SubscriptionCategory, on_delete=models.CASCADE, null=True)

    def __str__(self):
        if self.category==None:
            return f"No category, {self.start}, {self.end}"
        return f"{self.category.title}, {self.start}, {self.end}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    active = models.BooleanField(blank=True, null=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}, ({self.user.username})"

