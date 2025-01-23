#!/bin/bash

# Wait for the database to be ready
echo "Waiting for the database..."
while ! nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for the database..."
  sleep 1
done
echo "Database is ready!"

# Wait for Redis to be ready (optional, depending on usage)
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  echo "Waiting for Redis..."
  sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec "$@"
