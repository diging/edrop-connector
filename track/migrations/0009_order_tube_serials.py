# Generated by Django 5.1.4 on 2025-01-31 04:31

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0008_remove_order_return_tracking_nr_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='tube_serials',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(), blank=True, null=True, size=None),
        ),
    ]
