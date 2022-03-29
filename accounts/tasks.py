import logging

from celery import shared_task
from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from .models import Profile
from datetime import date, timedelta

# Get an instance of a logger
logger = logging.getLogger(__name__)

@shared_task
def send_reminder_subscription_email():
    profiles = Profile.objects.all()
    for profile in profiles:
        if profile.subscription:
            if profile.subscription.end == date.today()+timedelta(days = 7):
                html_message = render_to_string('accounts/email/base_email.html', {'context': 'values'})
                send_mail(
                    subject='Your subscription exired in 7 days',
                    from_email=None,
                    message = _("Your subscription exired in 7 days"),
                    recipient_list = [profile.user.email],
                    html_message=html_message
                )
                logger.info('Reminder sent: ' + profile.user.first_name + " " + profile.user.last_name + "(" +  profile.user.email + ")")






