# Generated by Django 3.2.16 on 2022-10-30 18:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('machines', '0023_card_url_resolver'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='url_resolver',
        ),
    ]
