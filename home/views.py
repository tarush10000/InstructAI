from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login  # Renamed import
from django.contrib.auth import authenticate
from .forms import CustomUserCreationForm

def home_page(request):
    return render(request, 'home/index.html')

def signup(request):
    if request.method == 'POST':
        print("chal agay")
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Use renamed import
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'home/signup.html', {'form': form})

def login(request):  # Renamed from 'login'
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)  # Use renamed import
            return redirect('home')
        else:
            return render(request, 'home/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'home/login.html')