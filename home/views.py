import os
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.auth import login as auth_login
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

def home(request):
    return render(request, 'home/dashboard.html')

def video(request):
    return render(request, 'home/video.html')

VIDEO_LEARNING_DIR = os.path.join(settings.MEDIA_ROOT, 'Video_Learning')
os.makedirs(VIDEO_LEARNING_DIR, exist_ok=True)

def video_page(request):
    form = VideoGenerationForm()
    # Optional: Fetch past videos from the database
    # past_videos = Video.objects.all().order_by('-created_at')
    past_videos = get_past_videos() # Implement this function to fetch from filesystem
    return render(request, 'home/video.html', {'form': form, 'past_videos': past_videos})

def get_past_videos():
    videos = []
    for filename in os.listdir(VIDEO_LEARNING_DIR):
        if filename.endswith('.mp4'):
            video_name = filename[:-4].replace('_', ' ').title()
            videos.append({'name': video_name, 'filename': filename})
    return videos

@require_POST
def generate_video(request):
    form = VideoGenerationForm(request.POST, request.FILES)
    if form.is_valid():
        topic = form.cleaned_data['topic']
        files = request.FILES.getlist('files')

        extracted_text = ""
        fs = FileSystemStorage()
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)

        try:
            for file in files:
                file_path = os.path.join(temp_dir, file.name)
                fs.save(file_path, file)
                file_extension = os.path.splitext(file.name)[1].lower()

                if file_extension == '.pdf':
                    try:
                        from pdfminer.high_level import extract_text as pdf_extract_text
                        extracted_text += pdf_extract_text(file_path) + "\n\n"
                    except ImportError:
                        return HttpResponse("Error: pdfminer.six is not installed. Please install it: pip install pdfminer.six")
                elif file_extension in ['.ppt', '.pptx']:
                    try:
                        from pptx import Presentation
                        prs = Presentation(file_path)
                        for slide in prs.slides:
                            for shape in slide.shapes:
                                if shape.has_text_frame:
                                    for paragraph in shape.text_frame.paragraphs:
                                        for run in paragraph.runs:
                                            extracted_text += run.text + "\n"
                                    extracted_text += "\n"
                    except ImportError:
                        return HttpResponse("Error: python-pptx is not installed. Please install it: pip install python-pptx")
                elif file_extension in ['.doc', '.docx']:
                    try:
                        from docx import Document
                        document = Document(file_path)
                        for paragraph in document.paragraphs:
                            extracted_text += paragraph.text + "\n"
                        extracted_text += "\n"
                    except ImportError:
                        return HttpResponse("Error: python-docx is not installed. Please install it: pip install python-docx")
                os.remove(file_path) # Remove temporary file
        except Exception as e:
            return HttpResponse(f"Error processing files: {e}")
        finally:
            # Clean up the temporary directory
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting temporary file: {e}")

        try:
            video_filename = f'{topic.replace(" ", "_")}_video.mp4'
            transcript_filename = f'{topic.replace(" ", "_")}_transcript.txt'
            video_output_path = os.path.join(VIDEO_LEARNING_DIR, video_filename)
            transcript_output_path = os.path.join(VIDEO_LEARNING_DIR, transcript_filename)

            # Modify your main_with_input function to return the transcript
            transcript = video_script.main_with_input(topic, extracted_text, video_output_path, transcript_output_path) # Pass output paths

            # Optional: Save video information to the database
            # Video.objects.create(title=topic, video_file=os.path.join('Video_Learning', video_filename), transcript_file=os.path.join('Video_Learning', transcript_filename))

            # Redirect to the video page to show the updated list
            return render(request, 'home/video.html', {'form': VideoGenerationForm(), 'generation_success': True, 'past_videos': get_past_videos()})

        except Exception as e:
            return HttpResponse(f"Error during video generation: {e}")
    else:
        return render(request, 'home/video.html', {'form': form, 'errors': form.errors, 'past_videos': get_past_videos()})

def video_view(request, video_filename):
    video_path = os.path.join(VIDEO_LEARNING_DIR, video_filename)
    transcript_filename = video_filename.replace('_video.mp4', '_transcript.txt')
    transcript_path = os.path.join(VIDEO_LEARNING_DIR, transcript_filename)
    transcript_content = ""
    try:
        with open(transcript_path, 'r') as f:
            transcript_content = f.read()
    except FileNotFoundError:
        transcript_content = "Transcript not found."

    return render(request, 'home/video_view.html', {'video_path': os.path.join(settings.MEDIA_URL, 'Video_Learning', video_filename), 'transcript': transcript_content})

