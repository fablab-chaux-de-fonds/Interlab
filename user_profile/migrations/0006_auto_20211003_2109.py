# Generated by Django 3.1.13 on 2021-10-03 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0005_auto_20211003_2106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptioncategory',
            name='duration',
            field=models.PositiveSmallIntegerField(blank=True, default=360),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subscriptioncategory',
            name='sort',
            field=models.PositiveSmallIntegerField(blank=True, default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='subscriptioncategory',
            name='star_flag',
            field=models.BooleanField(blank=True, default=False),
            preserve_default=False,
        ),
    ]