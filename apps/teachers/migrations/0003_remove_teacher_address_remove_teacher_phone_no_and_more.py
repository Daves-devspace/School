# Generated by Django 5.1.5 on 2025-01-21 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0002_teacher_staff_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='address',
        ),
        migrations.RemoveField(
            model_name='teacher',
            name='phone_no',
        ),
        migrations.RemoveField(
            model_name='teacher',
            name='role',
        ),
        migrations.AddField(
            model_name='teacher',
            name='is_headteacher',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='full_name',
            field=models.CharField(max_length=50),
        ),
    ]
