#!/bin/bash
# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z -v -w30 $DB_HOST $DB_PORT; do
  echo "Waiting for database connection..."
  sleep 1
done
echo "PostgreSQL is up!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z -v -w30 $REDIS_HOST 6379; do
  echo "Waiting for Redis connection..."
  sleep 1
done
echo "Redis is up!"

# Run Django app
exec "$@"
