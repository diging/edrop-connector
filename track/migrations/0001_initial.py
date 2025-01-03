# Generated by Django 5.1 on 2025-01-03 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_id', models.CharField(max_length=255)),
                ('initiated_by', models.CharField(max_length=255)),
                ('redcap_url', models.CharField(max_length=255)),
                ('project_url', models.CharField(max_length=255)),
                ('record_id', models.CharField(max_length=255)),
                ('tracking_nr', models.CharField(max_length=255)),
                ('order_status', models.CharField(choices=[('IN', 'Initiated'), ('PR', 'In Progress'), ('DO', 'Completed')], max_length=3)),
            ],
        ),
    ]
