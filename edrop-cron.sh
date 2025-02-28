#!/bin/bash

NAME="edrop"                                  # Name of the application
DJANGODIR=/edrop                              # Django project directory
NUM_WORKERS=3                                 # Number of Gunicorn workers
DJANGO_SETTINGS_MODULE=edrop.settings         # Django settings module
DJANGO_WSGI_MODULE=edrop.wsgi                 # WSGI module name

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source .env_app
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
mkdir -p /edrop/logs

while true; do 
    sleep 5;
    http_response=$(curl -s -o /dev/null -I -w "%{http_code}\n" http://localhost:8000/$APP_ROOT);
    if [ $http_response == "200" ]; then
        break
    else
        echo "eDrop not responding"
    fi
done
echo "eDrop has started successfully"

# start the cron job
python manage.py runapscheduler