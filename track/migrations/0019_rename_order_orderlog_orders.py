# Generated by Django 5.1 on 2025-01-24 23:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0018_orderlog_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderlog',
            old_name='order',
            new_name='orders',
        ),
    ]
