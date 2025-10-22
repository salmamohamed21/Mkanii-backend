#!/bin/bash
set -o errexit  # stop the script if any command fails

python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn mkani.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --chdir mkani
