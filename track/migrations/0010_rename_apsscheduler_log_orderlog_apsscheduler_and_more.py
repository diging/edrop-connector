# Generated by Django 5.1 on 2025-01-24 19:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0009_orderlog'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderlog',
            old_name='apsscheduler_log',
            new_name='apsscheduler',
        ),
        migrations.RenameField(
            model_name='orderlog',
            old_name='redcap_log',
            new_name='redcap',
        ),
    ]
