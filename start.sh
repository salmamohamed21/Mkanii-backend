#!/bin/bash
set -o errexit

# Print debug info
echo "Starting Mkani Backend..."
echo "Django Settings Module: $DJANGO_SETTINGS_MODULE"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start gunicorn
echo "Starting gunicorn..."
gunicorn wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --worker-class sync
