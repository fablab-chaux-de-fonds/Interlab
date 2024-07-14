import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator
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

def validate_update_opening_slot_on_machine_slot(opening_slot):
    from .models import MachineSlot

    # Get all machine slots related to the opening slot object.
    machine_slots = MachineSlot.objects.filter(opening_slot=opening_slot)

    # Check if any of the machine slots are outside the new opening slot.
    for machine_slot in machine_slots:
        if machine_slot.user and (machine_slot.start < opening_slot.start or machine_slot.end > opening_slot.end):
            raise ValidationError(
                mark_safe(_('You can not update the opening slot because {user} has already reserved the {machine} from {start_time} to {end_time}.').format(
                    start_time=machine_slot.start.strftime('%H:%M'),
                    end_time=machine_slot.end.strftime('%H:%M'),
                    user=machine_slot.user.first_name + ' ' + machine_slot.user.last_name,
                    machine=machine_slot.machine.title
                )),
                code='conflicting_reservation',
                params={'conflictive_reservation': machine_slot}
            )

def validate_delete_opening_slot(opening_slot):
    if not opening_slot.can_be_deleted:
        raise ValidationError(
            mark_safe(_('You cannot delete your opening slot because you have reservations')),
            code='opening_slot_has_reservation'
        )

def validate_delete_machine_slot(machine_slot):
    if machine_slot.user is not None: 
        raise ValidationError(
            mark_safe(_('You cannot delete your machine slot because you have reservations')),
            code='machine_slot_has_reservation'
        )

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator

def url_or_email_validator(value):
    url_validator = URLValidator()
    email_validator = EmailValidator()

    try:
        url_validator(value)
    except ValidationError:
        try:
            email_validator(value)
        except ValidationError:
            raise ValidationError('This field must be a valid URL or email address.')


def validate_attendees_within_available_slots(value, event_slot):
    if (
        event_slot.registration_limit != 0
        and value > event_slot.available_registration
    ):
        raise ValidationError(
            mark_safe(
                _(
                    "You cannot register more than {available_registration} peoples."
                ).format(available_registration=event_slot.available_registration)
            ),
            code="attendees_not_within_available_slots",
        )
