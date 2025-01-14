from django.shortcuts import render

import logging
logger = logging.getLogger(__name__)

def index(request):
    template = "track/home.html"
    context = {}
    return render(request, template, context)
