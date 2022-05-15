import os
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from .models import Profile
from datetime import date, timedelta

def send_reminder_subscription_email():
    profiles = Profile.objects.filter(subscription__end = date.today() + timedelta(days = 7))
    for profile in profiles:
        context = {
            'profile': profile,
            'DOMAIN': Site.objects.first().domain
        }
        html_message = render_to_string('accounts/email/subscription_reminder.html', context)
        send_mail(
            subject=_('Your subscription will expire in 7 days'),
            from_email=None,
            message = _("Your subscription will expire in 7 days"),
            recipient_list = [profile.user.email],
            html_message=html_message
        )
    return(list(profiles))