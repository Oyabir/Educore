# Generated by Django 5.1 on 2024-09-09 12:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platformTK', '0025_alter_competitions_group_alter_competitions_prof'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sections',
            name='competition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sections', to='platformTK.competitions'),
        ),
    ]
