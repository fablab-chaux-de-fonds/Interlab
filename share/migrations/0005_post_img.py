# Generated by Django 3.2.16 on 2023-01-21 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0004_remove_post_img'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='img',
            field=models.ImageField(blank=True, null=True, upload_to='share'),
        ),
    ]
