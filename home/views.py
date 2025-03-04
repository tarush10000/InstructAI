from django.shortcuts import render

# Create your views here.

def home_page(request):
    return render(request, 'home/index.html')

def signup(request):
    return render(request, 'home/signup.html')

def login(request):
    return render(request, 'home/login.html')