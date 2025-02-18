# Generated by Django 5.1 on 2025-01-30 21:43

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0020_rename_runapscheduler_orderlog_apscheduler_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfirmationCheckLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apscheduler', models.TextField(blank=True, default='', null=True)),
                ('orders', models.TextField(blank=True, default='', null=True)),
                ('gbf', models.TextField(blank=True, default='', null=True)),
                ('redcap', models.TextField(blank=True, default='', null=True)),
                ('is_complete', models.BooleanField(default=False)),
                ('start_time', models.DateTimeField(default=datetime.datetime(2025, 1, 30, 21, 43, 11, 843965, tzinfo=datetime.timezone.utc))),
                ('job_id', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RenameField(
            model_name='orderlog',
            old_name='is_completed',
            new_name='is_complete',
        ),
        migrations.AddField(
            model_name='orderlog',
            name='start_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 1, 30, 21, 43, 11, 843965, tzinfo=datetime.timezone.utc)),
        ),
    ]
