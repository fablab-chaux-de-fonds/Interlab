from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.tasks import Schedule

class Command(BaseCommand):
    help = 'Create requiered Django Q tasks for subscription reminders'
    def handle(self, *args, **options):
        defaults = { 'schedule_type': Schedule.DAILY, 'next_run': timezone.now(), 'task': None }
        Schedule.objects.update_or_create(name='Accounts.Reminder', func='accounts.tasks.send_reminder_subscription_email', defaults=defaults)
        Schedule.objects.update_or_create(name='Accounts.Expired', func='accounts.tasks.send_expire_subscription_email', defaults=defaults)