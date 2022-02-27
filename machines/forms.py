from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Training


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = '__all__'
