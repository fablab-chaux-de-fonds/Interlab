from django.db import models

from accounts.models import Profile

class Post(models.Model):
    title = models.CharField(max_length=255)
    img = models.ImageField(upload_to='share')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

