# Generated by Django 5.1 on 2024-09-09 16:27

import platformTK.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platformTK', '0029_alter_etudiant_etudiantcode_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prof',
            name='ProfCode',
            field=models.CharField(blank=True, default=platformTK.models.generate_prof_code, max_length=100, null=True, unique=True),
        ),
    ]
