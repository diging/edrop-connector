from django.shortcuts import render


def index(request):
    template = "track/home.html"
    context = {}
    return render(request, template, context)
