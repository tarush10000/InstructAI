from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home_page, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('home/', views.home, name='dashboard'),
    path('video/', views.video_page, name='video'),
    path('generate/', views.generate_video, name='generate_video'),
    path('view_video/<str:video_filename>/', views.video_view, name='video_view'),
    path('video/<str:video_filename>/', views.video_view, name='video_view'),
    path('quiz/', views.quiz_page, name='quiz'),
    path('start_quiz/', views.start_quiz, name='start_quiz'),
    path('quiz_attempt/<uuid:quiz_session_id>/', views.quiz_attempt, name='quiz_attempt'),
    path('submit_quiz/', views.submit_quiz, name='submit_quiz'),
    path('quiz_result/<int:score>/<int:total>/', views.quiz_result, name='quiz_result'),
    path('notes/', views.notes_page, name='notes'),
    path('generate_notes/', views.generate_notes, name='generate_notes'),
    path('download_notes/<str:filename>/', views.download_notes, name='download_notes'),
    path('setting/', views.setting_page, name='setting'),
    path('interview/', views.interview_page, name='interview')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)