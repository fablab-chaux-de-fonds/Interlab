from django import forms
from .models import TypewriterPlugin

class TypewriterPluginForm(forms.ModelForm):
    class Meta:
        model = TypewriterPlugin
        fields = ['strings']
