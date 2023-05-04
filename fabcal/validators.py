import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


def validate_conflicting_openings(start, end, instance=None):
    from .models import OpeningSlot # import here to avoid circular imports
    
    conflicting_openings = OpeningSlot.objects.filter(
        start__lte=end,
        end__gte=start
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
                start_time=start.strftime('%H:%M'),
                end_time=end.strftime('%H:%M'),
                openings='<br>'.join(conflicting_times),
            )),
            code='conflicting_openings',
            params={'conflicting_openings': conflicting_openings}
        )

def validate_time_range(start, end):
    if start and end and start >= end:
        raise ValidationError(_("Start time after end time."), code='invalid_time_range')
