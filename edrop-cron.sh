#!/bin/bash

NAME="edrop"                                  # Name of the application
DJANGODIR=/edrop                              # Django project directory
NUM_WORKERS=3                                 # Number of Gunicorn workers
DJANGO_SETTINGS_MODULE=edrop.settings         # Django settings module
DJANGO_WSGI_MODULE=edrop.wsgi                 # WSGI module name
URL=127.0.0.1                                 # URL to ping before starting cron job
PORT=8000                                     # Port to ping before starting cron job

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source .env_app
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
mkdir -p /edrop/logs

while ! nc -z $URL $PORT; do echo "eDrop not responding"; sleep 5; done
echo "eDrop has started successfully"

# start the cron job
python manage.py runapscheduler