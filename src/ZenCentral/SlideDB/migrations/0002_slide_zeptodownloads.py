# Generated by Django 2.0 on 2018-02-13 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SlideDB', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='zeptoDownloads',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]