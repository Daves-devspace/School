#!/bin/bash

# Ensure environment variables are set
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
  echo "ERROR: DB_HOST and DB_PORT environment variables must be set."
  exit 1
fi

# Wait for the PostgreSQL database to be available
echo "Waiting for database connection at $DB_HOST:$DB_PORT..."
until nc -z -v -w30 $DB_HOST $DB_PORT; do
  echo "Database not ready. Retrying..."
  sleep 1
done
echo "Database connection established."

# Apply database migrations (only running migrate, not makemigrations)
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (this may be skipped if not necessary)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django application
echo "Starting application..."
exec "$@"
