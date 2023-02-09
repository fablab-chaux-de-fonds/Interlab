# Generated by Django 3.2.17 on 2023-02-09 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_squashed_0006_alter_profile_public_contact_plateform'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='public_contact',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Public contact'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='public_contact_plateform',
            field=models.CharField(blank=True, choices=[('discord', 'Discord'), ('instagram', 'Instagram'), ('facebook', 'Facebook'), ('linkedin', 'Linkedin'), ('envelope', 'e-mail')], max_length=255, null=True, verbose_name='Plublic chanel'),
        ),
    ]
