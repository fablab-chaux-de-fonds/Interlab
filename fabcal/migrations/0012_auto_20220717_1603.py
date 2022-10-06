# Generated by Django 3.2.13 on 2022-07-17 16:03

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fabcal', '0011_eventslot_subscriptions_limit'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eventslot',
            old_name='has_subscriptions',
            new_name='has_registration',
        ),
        migrations.RenameField(
            model_name='eventslot',
            old_name='subscriptions_limit',
            new_name='registration_limit',
        ),
        migrations.RemoveField(
            model_name='eventslot',
            name='subscriptions',
        ),
        migrations.AddField(
            model_name='eventslot',
            name='registrations',
            field=models.ManyToManyField(blank=True, null=True, related_name='event_registration_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
