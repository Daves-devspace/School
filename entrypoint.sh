#!/bin/bash

# Wait for the MySQL database to be available
echo "Waiting for database connection at $DB_HOST:$DB_PORT..."
until nc -z -v -w30 $DB_HOST $DB_PORT; do
  echo "Database not ready. Retrying..."
  sleep 1
done

echo "Database connection established. Proceeding..."

# Run collectstatic only if necessary
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations (optional but recommended)
echo "Running database migrations..."
python manage.py migrate --noinput

# Run the Django server using Gunicorn
exec "$@"
