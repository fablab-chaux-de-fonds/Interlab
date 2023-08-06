import django_filters
from django import forms

from .models import SuperUserProfile
from machines.models import Workshop, MachineCategory, Training

class SuperUserFilter(django_filters.FilterSet):

    trainer = django_filters.ModelMultipleChoiceFilter(
        queryset=Training.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        conjoined=True
    )

    technique = django_filters.ModelMultipleChoiceFilter(
        queryset=Workshop.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        conjoined=True
    )

    machine_category = django_filters.ModelMultipleChoiceFilter(
        queryset=MachineCategory.objects.filter(superuser_skill = True),
        widget=forms.CheckboxSelectMultiple(),
        conjoined=True
    )

    class Meta:
        model = SuperUserProfile
        fields = ['trainer', 'technique', 'machine_category']