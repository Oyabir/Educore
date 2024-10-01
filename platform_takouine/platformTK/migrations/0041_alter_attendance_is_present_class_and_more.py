# Generated by Django 5.1 on 2024-09-23 14:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platformTK', '0040_alter_attendance_is_present_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='is_present',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('schedule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classes', to='platformTK.schedule')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='attendance',
            name='class_instance',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='platformTK.class'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('student', 'schedule', 'class_instance', 'date')},
        ),
    ]