# Generated by Django 5.1.5 on 2025-01-19 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('author', models.CharField(max_length=100)),
                ('year', models.DateField()),
                ('subject', models.CharField(max_length=100)),
                ('isbn', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('level', models.IntegerField(unique=True)),
            ],
            options={
                'ordering': ['level'],
            },
        ),
        migrations.CreateModel(
            name='GradeSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'ordering': ['grade__level', 'section__name'],
            },
        ),
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('mobile', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('address', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'verbose_name_plural': 'Parents',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merchant_request_id', models.CharField(max_length=100)),
                ('checkout_request_id', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=30, null=True)),
                ('amount', models.IntegerField()),
                ('status', models.CharField(default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'db_table': 'payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], max_length=10)),
                ('date_of_birth', models.DateField()),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Graduated', 'Graduated')], default='Active', max_length=10)),
                ('sponsored', models.BooleanField(default=False)),
                ('religion', models.CharField(choices=[('Christian', 'Christian'), ('Muslim', 'Muslim'), ('Other', 'Other')], max_length=10)),
                ('joining_date', models.DateField()),
                ('admission_number', models.CharField(max_length=15, unique=True)),
                ('student_image', models.ImageField(blank=True, null=True, upload_to='students')),
                ('last_promoted', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StudentParent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relationship', models.CharField(choices=[('Father', 'Father'), ('Mother', 'Mother'), ('Guardian', 'Guardian'), ('Other', 'Other')], max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('expected_return_date', models.DateField()),
                ('return_date', models.DateField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'db_table': 'transactions',
                'ordering': ['-created_at'],
            },
        ),
    ]
