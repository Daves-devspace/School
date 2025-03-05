#!/bin/bash

# Function to log with timestamp
log() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Wait for the database to be ready
log "Waiting for the database..."
while ! nc -z $DB_HOST $DB_PORT; do
  log "Waiting for the database..."
  sleep 1
done
log "Database is ready!"

# Wait for Redis to be ready (ensure REDIS_PORT is set to 6379)
log "Waiting for Redis..."
while ! nc -z $REDIS_HOST 6379; do
  log "Waiting for Redis..."
  sleep 1
done
log "Redis is ready!"

# Run database migrations
log "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
log "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
log "Starting Gunicorn..."
exec "$@"
