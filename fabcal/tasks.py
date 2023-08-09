from datetime import datetime, timedelta

from django.db.models import Count, OuterRef, Subquery

from .models import OpeningSlot, MachineSlot

def remove_openingslot_if_on_reservation():
    one_day_after = datetime.now() + timedelta(days=1)

    reserved_opening_slots = MachineSlot.objects.filter(
        user__isnull=True,
        opening_slot=OuterRef('pk')
    )

    OpeningSlot.objects.filter(
        opening__is_reservation_mandatory=True,
        start__gte=one_day_after,
        start__lt=one_day_after + timedelta(hours=1),
        machineslot__in=Subquery(reserved_opening_slots.values('opening_slot'))
    ).delete()