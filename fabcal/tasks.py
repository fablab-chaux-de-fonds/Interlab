from datetime import datetime, timedelta

from django.db.models import Count, OuterRef, Subquery

from .models import OpeningSlot, MachineSlot

def remove_openingslot_if_on_reservation():
    now = datetime.now()

    reserved_opening_slots = MachineSlot.objects.filter(
        user__isnull=True,
        opening_slot=OuterRef('pk')
    )

    OpeningSlot.objects.filter(
        opening__is_reservation_mandatory=True,
        start__gte=now,
        start__lt=now + timedelta(days=1),
        machineslot__in=Subquery(reserved_opening_slots.values('opening_slot'))
    ).delete()