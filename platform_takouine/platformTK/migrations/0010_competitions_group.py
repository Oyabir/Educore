# Generated by Django 5.1 on 2024-08-26 11:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platformTK', '0009_sections_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitions',
            name='group',
            field=models.ForeignKey(default=16, on_delete=django.db.models.deletion.CASCADE, related_name='competitions', to='platformTK.groups'),
            preserve_default=False,
        ),
    ]