# Generated by Django 3.2.15 on 2022-10-15 10:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('machines', '0006_auto_20221015_0954'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tool',
            name='about',
        ),
    ]