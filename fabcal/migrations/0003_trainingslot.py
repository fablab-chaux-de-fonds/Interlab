# Generated by Django 3.2.15 on 2022-10-13 07:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('machines', '0003_training_is_active'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fabcal', '0002_auto_20221003_1853'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('opening_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fabcal.openingslot')),
                ('training', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='machines.training')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]