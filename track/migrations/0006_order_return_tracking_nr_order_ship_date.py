# Generated by Django 5.1 on 2025-01-21 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0005_alter_order_initiated_by_alter_order_order_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='return_tracking_nr',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='ship_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
