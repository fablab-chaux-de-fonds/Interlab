from tkinter import Widget
import django_filters

from django import forms

from .models import Machine, Workshop, Material, Training, MachineCategory

class MachineFilter(django_filters.FilterSet):

    workshop = django_filters.ModelMultipleChoiceFilter(
        queryset=Workshop.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        conjoined=True
    )

    material = django_filters.ModelMultipleChoiceFilter(
        queryset=Material.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        conjoined=True
    )

    class Meta:
        model = Machine
        fields = ['workshop', 'material']

class TrainingFilter(django_filters.FilterSet):

    machine_category = django_filters.ModelMultipleChoiceFilter(
        queryset=MachineCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        conjoined=True
    )

    class Meta:
        model = Training
        fields = ['machine_category']