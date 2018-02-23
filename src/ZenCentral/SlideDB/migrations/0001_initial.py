# Generated by Django 2.0 on 2018-02-22 15:47

import SlideDB.models
from django.db import migrations, models
import django.db.models.deletion
import enumfields.fields
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('enabled', models.BooleanField()),
                ('zeptoId', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Construct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('enabled', models.BooleanField()),
                ('zeptoId', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Slide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pptFile', models.URLField()),
                ('enabled', models.BooleanField()),
                ('thumbnailFile', models.URLField()),
                ('hasIcon', models.BooleanField()),
                ('hasImage', models.BooleanField()),
                ('layout', enumfields.fields.EnumField(default=0, enum=SlideDB.models.LayoutChoices, max_length=10)),
                ('style', enumfields.fields.EnumField(default=0, enum=SlideDB.models.StyleChoices, max_length=10)),
                ('zeptoId', models.IntegerField(unique=True)),
                ('zeptoDownloads', models.IntegerField()),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slides', to='SlideDB.Construct')),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
        ),
        migrations.CreateModel(
            name='SubConcept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('enabled', models.BooleanField()),
                ('zeptoId', models.IntegerField(unique=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subConcepts', to='SlideDB.Concept')),
            ],
        ),
        migrations.AddField(
            model_name='construct',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='constructs', to='SlideDB.SubConcept'),
        ),
    ]
