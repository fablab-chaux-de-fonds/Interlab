from datetime import datetime, timedelta

from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db.models import Count, OuterRef, Subquery
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .models import OpeningSlot, MachineSlot

def remove_openingslot_if_on_reservation():
    site = Site.objects.get(pk=1)
    one_day_after = datetime.now() + timedelta(days=1)

    openings_slots = OpeningSlot.objects.filter(
        opening__is_reservation_mandatory=True,
        start__gte=one_day_after,
        start__lt=one_day_after + timedelta(hours=1)
    )

    for object in openings_slots:
        if object.can_be_deleted:
            object.delete()
            html_message = render_to_string('fabcal/email/openingslot_auto_delete.html', {'object': object, 'domain': site.domain})
            send_mail(
                from_email = None,
                subject = _('No reservation - your opening slot has been deleted'),
                message = _('No reservation - your opening slot has been deleted'),
                recipient_list = [object.user.email],
                html_message = html_message
            )
        else:
            html_message = render_to_string('fabcal/email/openingslot_confirm.html', {'object': object, 'domain': site.domain})
            send_mail(
                from_email = None,
                subject = _('You have reservation - your opening slot is confirmed'),
                message = _('You have reservation - your opening slot is confirmed'),
                recipient_list = [object.user.email],
                html_message = html_message
            )