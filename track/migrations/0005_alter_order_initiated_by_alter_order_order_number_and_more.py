# Generated by Django 5.1 on 2025-01-14 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('track', '0004_alter_order_initiated_by_alter_order_order_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='initiated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(blank=True, choices=[('PE', 'Pending'), ('IN', 'Initiated'), ('SH', 'Kit has shipped'), ('DO', 'Completed')], max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='project_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='redcap_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_nr',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
