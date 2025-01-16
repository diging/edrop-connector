# Generated by Django 5.1 on 2025-01-14 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0002_order_order_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('PE', 'Pending'), ('IN', 'Initiated'), ('SH', 'Kit has shipped'), ('DO', 'Completed')], max_length=3),
        ),
    ]
