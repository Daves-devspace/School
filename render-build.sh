#!/usr/bin/env bash

# Install dependencies
pip install -r requirements.txt

# Make migrations (to generate migration files)
python manage.py makemigrations --noinput


# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
python manage.py shell <<EOF
from django.contrib.auth.models import User
import os

# Fetch values from environment variables
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')

# Check if superuser exists, and create if not
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
EOF
