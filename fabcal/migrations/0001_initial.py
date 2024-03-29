# Generated by Django 3.2.16 on 2022-11-16 20:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('openings', '0009_auto_20220712_2148'),
        ('openings', '0001_initial'),
        ('cms', '0022_auto_20180620_1551'),
        ('machines', '0002_PR130'),
        ('machines', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarOpeningsPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='fabcal_calendaropeningspluginmodel', serialize=False, to='cms.cmsplugin')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='EventsListPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='fabcal_eventslistpluginmodel', serialize=False, to='cms.cmsplugin')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='WeeklyPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='fabcal_weeklypluginmodel', serialize=False, to='cms.cmsplugin')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='OpeningSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('opening', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='openings.opening')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Opening Slot',
                'verbose_name_plural': 'Opening Slots',
            },
        ),
        migrations.CreateModel(
            name='EventSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('has_registration', models.BooleanField()),
                ('registration_limit', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('price', models.TextField(max_length=255)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='openings.event')),
                ('opening_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fabcal.openingslot')),
                ('registrations', models.ManyToManyField(blank=True, null=True, related_name='event_registration_users', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Event Slot',
                'verbose_name_plural': 'Event Slots',
            },
        ),
        migrations.CreateModel(
            name='TrainingSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('opening_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fabcal.openingslot')),
                ('training', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='machines.training')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('registration_limit', models.IntegerField(blank=True, null=True)),
                ('registrations', models.ManyToManyField(blank=True, null=True, related_name='training_registration_users', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Training Slot',
                'verbose_name_plural': 'Training Slots',
            },
        ),
        migrations.CreateModel(
            name='MachineSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('machine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='machines.machine')),
                ('opening_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fabcal.openingslot')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Machine Slot',
                'verbose_name_plural': 'Machine Slots',
            },
        ),
    ]
