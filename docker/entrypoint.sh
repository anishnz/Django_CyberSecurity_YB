#!/bin/sh
# Runs before the web server starts: database tables, static files, first-run demo data.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput -v0
python manage.py seed_demo
exec "$@"
