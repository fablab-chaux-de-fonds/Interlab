# Generated by Django 3.2.17 on 2023-02-09 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('machines', '0006_merge_20230209_2150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='training',
            name='includ_free_machine_voucher',
            field=models.BooleanField(default=True, verbose_name='Inclus bon machine'),
        ),
    ]
