# Generated by Django 5.1 on 2025-02-03 22:40

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0027_alter_confirmationchecklog_end_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmationchecklog',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 3, 22, 40, 10, 902936, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='orderlog',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 3, 22, 40, 10, 902936, tzinfo=datetime.timezone.utc)),
        ),
    ]
