# Generated by Django 2.0 on 2018-02-09 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Search', '0003_auto_20180124_0246'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchIndex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False)),
            ],
        ),
    ]
