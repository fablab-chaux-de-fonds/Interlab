import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import OpeningSlot
from django.utils.safestring import mark_safe


def validate_conflicting_openings(date, start_time, end_time, instance=None):
    if date and start_time and end_time:
        conflicting_openings = OpeningSlot.objects.filter(
            start__lte=datetime.datetime.combine(date, end_time),
            end__gte=datetime.datetime.combine(date, start_time)
        )
        if instance:
            conflicting_openings = conflicting_openings.exclude(pk=instance.pk)
        
        if conflicting_openings.exists():
            conflicting_times = [
                f"{opening.start.strftime('%H:%M')} - {opening.end.strftime('%H:%M')}: {opening.user.first_name}"
                for opening in conflicting_openings
            ]
            raise forms.ValidationError(
                mark_safe(_('The time slot ({start_time} - {end_time}) conflicts with the following openings: <br> {openings}').format(
                    start_time=start_time.strftime('%H:%M'),
                    end_time=end_time.strftime('%H:%M'),
                    openings='<br>'.join(conflicting_times),
                )),
                code='conflicting_openings'
            )



def validate_time_range(date, start_time, end_time):
    if start_time and end_time and start_time >= end_time:
        raise ValidationError(_("Start time after end time."), code='invalid_time_range')
