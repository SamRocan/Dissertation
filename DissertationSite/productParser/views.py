from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, 'productParser/index.html')

def homepage(request):
    return render(request, 'productParser/home.html')

