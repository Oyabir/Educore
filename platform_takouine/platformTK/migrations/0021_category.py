# Generated by Django 5.1 on 2024-09-06 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platformTK', '0020_alter_commande_commande_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
    ]
