from django.db import models
from django.utils.translation import gettext as _

from accounts.models import Profile

class Post(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    img = models.ImageField(upload_to='share', verbose_name=_('Image'))
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name=_('User'))
    url = models.URLField(blank=True, null=True, verbose_name=_('Link'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

