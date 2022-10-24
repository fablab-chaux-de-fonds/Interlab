# Generated by Django 3.2.15 on 2022-10-15 09:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('machines', '0004_auto_20221013_0712'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tools',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('icon', models.ImageField(upload_to='icons', verbose_name='Icon')),
                ('title', models.CharField(max_length=255, verbose_name='Titre')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Description')),
                ('href', models.URLField(verbose_name='Lien')),
                ('about', models.ManyToManyField(to='machines.ItemForRent')),
            ],
        ),
        migrations.CreateModel(
            name='ToolsMachine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort', models.PositiveSmallIntegerField(default=1)),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='machines.training')),
                ('tool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='machines.tools')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ToolsTraining',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort', models.PositiveSmallIntegerField(default=1)),
                ('tool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='machines.tools')),
                ('training', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='machines.training')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='outcomelistitem',
            name='training',
        ),
        migrations.DeleteModel(
            name='DIYListItem',
        ),
        migrations.DeleteModel(
            name='OutcomeListItem',
        ),
    ]