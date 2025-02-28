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

# When a new container is being created, eDROP Connector takes a long time to startup because all dependencies
# need to be installed first. The cron job, however, needs all dependencies to be installed before it can start up.
# Since we know that once eDROP Connector is up and running, all dependencies are installed, we just wait till we
# get a 200 response from the web app before starting the cron job.
# Using the autorestart property of Supervisor does not seem to work when deployed in production, hence this work around.
while true; do 
    sleep 5;
    http_response=$(curl -s -o /dev/null -I -w "%{http_code}\n" http://localhost:8000/$APP_ROOT);
    if [ $http_response == "200" ]; then
        break
    else
        echo "eDROP Connector is not yet responding."
    fi
done
echo "eDROP Connector has started successfully"

# start the cron job
python manage.py runapscheduler