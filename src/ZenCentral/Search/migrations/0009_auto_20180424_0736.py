# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-24 07:36
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('SlideDB', '0001_initial'),
        ('Search', '0008_auto_20180423_0905'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='searchresultrating',
            unique_together=set([('user', 'slide', 'queryTemplate')]),
        ),
    ]
