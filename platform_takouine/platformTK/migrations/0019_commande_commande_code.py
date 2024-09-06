# Generated by Django 5.1 on 2024-09-06 11:23

import platformTK.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platformTK', '0018_alter_membership_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='commande_code',
            field=models.CharField(blank=True, default=platformTK.models.generate_commande_code, max_length=100, null=True),
        ),
    ]
