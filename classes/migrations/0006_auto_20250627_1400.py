# Generated by Django 3.2.25 on 2025-06-27 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0005_auto_20250627_1353'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fitnessclass',
            name='date',
        ),
        migrations.RemoveField(
            model_name='fitnessclass',
            name='time',
        ),
        migrations.AlterField(
            model_name='fitnessclass',
            name='title',
            field=models.CharField(default='Untitled Class', max_length=100),
        ),
    ]
