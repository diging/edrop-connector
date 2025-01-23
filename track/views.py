from django.shortcuts import render

import logging
logger = logging.getLogger(__name__)

def index(request):
    template = "track/home.html"
    # if there is a version file (which there should be after deployment)
    # we'll show this on the home page
    try:
        with open('edrop/static/VERSION.txt', 'r') as file:
            context = {
                'version': file.read()
            }
    except Exception as ex:
        logger.error("Could not get version.")
        logger.error(ex)
        context = {}

    return render(request, template, context)
