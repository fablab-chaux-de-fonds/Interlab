from tkinter import Widget
import django_filters

from django import forms

from .models import Machine, Workshop, Material

class MachineFilter(django_filters.FilterSet):

    workshop = django_filters.ModelMultipleChoiceFilter(
        queryset=Workshop.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    material = django_filters.ModelMultipleChoiceFilter(
        queryset=Material.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Machine
        fields = ['workshop', 'material']