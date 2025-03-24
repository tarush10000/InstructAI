from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('home/', views.home, name='dashboard'),
    path('video/', views.video, name='video'),
    path('generate/', views.generate_video, name='generate_video'),
    path('view_video/<str:video_filename>/', views.video_view, name='video_view'),
]