#!/bin/bash

# Wait for database and Redis to be ready
echo "Waiting for the database..."
while ! nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for the database..."
  sleep 1
done
echo "Database is ready!"

# Run database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec "$@"
