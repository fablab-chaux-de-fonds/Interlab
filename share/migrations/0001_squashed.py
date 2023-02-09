# Generated by Django 3.2.16 on 2023-01-21 15:06

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    replaces = [('share', '0001_initial'), ('share', '0002_auto_20230118_1633'), ('share', '0003_rename_user_post_profile'), ('share', '0004_remove_post_img'), ('share', '0005_post_img'), ('share', '0006_alter_post_img')]

    initial = True

    dependencies = [
        ('accounts', '0003_auto_20221222_0802'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.profile')),
                ('created_at', models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('img', models.ImageField(upload_to='share')),
            ],
        ),
    ]
