# Generated by Django 5.1 on 2025-02-11 20:01

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0032_remove_orderlog_apscheduler_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmationchecklog',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 11, 20, 1, 56, 543302, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='orderlog',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 11, 20, 1, 56, 543302, tzinfo=datetime.timezone.utc)),
        ),
    ]
