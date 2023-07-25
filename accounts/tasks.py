from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from .models import Profile
from datetime import date, timedelta

def get_context_base():
    return(
        {
            'DOMAIN': Site.objects.first().domain
        }
    )

def send_reminder_subscription_email():
    profiles = Profile.objects.filter(subscription__end = date.today() + timedelta(days = 7))
    for profile in profiles:
        context = get_context_base()
        context['profile'] = profile
        html_message = render_to_string('accounts/email/subscription_reminder.html', context)
        send_mail(
            from_email=None,
            subject = _('Your subscription expires in one week'),
            message = _("Your subscription expires in one week"),
            recipient_list = [profile.user.email],
            html_message=html_message
        )
    return(list(profiles))

def send_expire_subscription_email():
    profiles = Profile.objects.filter(subscription__end = date.today())
    for profile in profiles:
        context = get_context_base()
        context['profile'] = profile
        html_message = render_to_string('accounts/email/subscription_expire.html', context)
        send_mail(
            from_email = None,
            subject = _('Renew your subscription now'),
            message = _("Renew your subscription now"),
            recipient_list = [profile.user.email],
            html_message = html_message
        )
    return(list(profiles))