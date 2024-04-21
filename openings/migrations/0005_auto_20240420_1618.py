# Generated by Django 3.2.24 on 2024-04-20 16:18

import colorfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openings', '0004_alter_opening_desc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='img',
        ),
        migrations.AddField(
            model_name='event',
            name='photo',
            field=models.ImageField(default='/img/opening.jpg', upload_to='img', verbose_name='Photo'),
        ),
        migrations.AddField(
            model_name='opening',
            name='photo',
            field=models.ImageField(default='/img/opening.jpg', upload_to='img', verbose_name='Photo'),
        ),
        migrations.AlterField(
            model_name='event',
            name='background_color',
            field=colorfield.fields.ColorField(default='#0b1783', image_field=None, max_length=25, samples=[('#0b1783', 'blue'), ('#ddf9ff', 'blue-light'), ('#e3005c', 'red'), ('#ffe8e0', 'red-light'), ('#00a59f', 'green'), ('#e4f2e5', 'green-light')]),
        ),
        migrations.AlterField(
            model_name='event',
            name='color',
            field=colorfield.fields.ColorField(default='#ffffff', image_field=None, max_length=25, samples=[('#0b1783', 'blue'), ('#ddf9ff', 'blue-light'), ('#e3005c', 'red'), ('#ffe8e0', 'red-light'), ('#00a59f', 'green'), ('#e4f2e5', 'green-light')]),
        ),
        migrations.AlterField(
            model_name='opening',
            name='background_color',
            field=colorfield.fields.ColorField(default='#0b1783', image_field=None, max_length=25, samples=[('#0b1783', 'blue'), ('#ddf9ff', 'blue-light'), ('#e3005c', 'red'), ('#ffe8e0', 'red-light'), ('#00a59f', 'green'), ('#e4f2e5', 'green-light')]),
        ),
        migrations.AlterField(
            model_name='opening',
            name='color',
            field=colorfield.fields.ColorField(default='#ffffff', image_field=None, max_length=25, samples=[('#0b1783', 'blue'), ('#ddf9ff', 'blue-light'), ('#e3005c', 'red'), ('#ffe8e0', 'red-light'), ('#00a59f', 'green'), ('#e4f2e5', 'green-light')]),
        ),
    ]
