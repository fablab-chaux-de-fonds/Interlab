# Generated by Django 3.2.20 on 2023-08-03 21:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('machines', '0008_auto_20230803_2148'),
        ('cms', '0022_auto_20180620_1551'),
        ('accounts', '0008_merge_20230310_1915'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuperUserListPluginModel',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, related_name='accounts_superuserlistpluginmodel', serialize=False, to='cms.cmsplugin')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='SuperUserStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SuperUserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to='profile')),
                ('about_me', models.CharField(blank=True, max_length=255, null=True, verbose_name='About me')),
                ('machine_category', models.ManyToManyField(blank=True, null=True, to='machines.MachineCategory', verbose_name='machine category')),
                ('software', models.ManyToManyField(blank=True, null=True, to='machines.Software', verbose_name='software')),
                ('status', models.ManyToManyField(blank=True, null=True, to='accounts.SuperUserStatus', verbose_name='status')),
                ('technique', models.ManyToManyField(blank=True, null=True, to='machines.Workshop', verbose_name='technique')),
                ('trainer', models.ManyToManyField(blank=True, null=True, to='machines.Training', verbose_name='trainer')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]