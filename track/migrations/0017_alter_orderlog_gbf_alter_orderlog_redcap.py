# Generated by Django 5.1 on 2025-01-24 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0016_alter_orderlog_runapscheduler'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderlog',
            name='gbf',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='orderlog',
            name='redcap',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
