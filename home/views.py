import os
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .forms import VideoGenerationForm
import importlib.util
import sys

# Create your views here.
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate
from .forms import CustomUserCreationForm

def home_page(request):
    return render(request, 'home/index.html')
def quiz_page(request):
    return render(request, 'home/quiz.html')
def notes_page(request):
    return render(request, 'home/notes.html')
def setting_page(request):
    return render(request, 'home/setting.html')
def interview_page(request):
    return render(request, 'home/interview.html')
def video_page(request):
    return render(request, 'home/video.html')
def signup(request):
    if request.method == 'POST':
        print("chal agay")
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # Use renamed import
            return render(request, 'home/dashboard.html')
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
            return render(request, 'home/dashboard.html')
        else:
            return render(request, 'home/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'home/login.html')

def home(request):
    return render(request, 'home/dashboard.html')

# Removed the direct imports of video_gen
# from .video_gen import *
# from . import video_gen

VIDEO_LEARNING_DIR = os.path.join(settings.MEDIA_ROOT, 'Video_Learning')
os.makedirs(VIDEO_LEARNING_DIR, exist_ok=True)

def video_page(request):
    form = VideoGenerationForm()
    past_videos = get_past_videos()
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
    form = VideoGenerationForm(request.POST, request.FILES, request=request)
    if form.is_valid():
        topic = form.cleaned_data['topic']
        uploaded_file = request.FILES.get('files') # Get a single file

        extracted_text = ""
        fs = FileSystemStorage()
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        os.makedirs(temp_dir, exist_ok=True)

        try:
            file = uploaded_file # Use the single uploaded file
            file_path = os.path.join(temp_dir, file.name)
            fs.save(file_path, file)
            file_extension = os.path.splitext(file.name)[1].lower()

            if file_extension == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        extracted_text = ""
                        for page_num in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_num]
                            extracted_text += page.extract_text() + "\n\n"
                except ImportError:
                    return HttpResponse("Error: PyPDF2 is not installed. Please install it: pip install PyPDF2")
                except Exception as e:
                    return HttpResponse(f"Error during PDF processing with PyPDF2: {e}")
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
            return HttpResponse(f"Error processing file: {e}")
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

            # Import the video_gen module using importlib
            import importlib
            module_name = 'home.video_gen'
            module = importlib.import_module(module_name)

            script = generate_script(extracted_text, topic)

            # Call the video generation script
            transcript_content = module.main_with_input(topic, script, video_output_path, transcript_output_path)

            # Write the transcript file explicitly with UTF-8 encoding
            try:
                with open(transcript_output_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_content)
            except Exception as e:
                print(f"Error writing transcript file: {e}")

            return render(request, 'home/video.html', {'form': VideoGenerationForm(), 'generation_success': True, 'past_videos': get_past_videos()})

        except ImportError as e:
            return HttpResponse(f"Error during video generation (import): {e}")
        except Exception as e:
            return HttpResponse(f"Error during video generation: {e}")
    else:
        return render(request, 'home/video.html', {'form': form, 'errors': form.errors, 'past_videos': get_past_videos()})

import google.generativeai as genai

def generate_script(extracted_text, topic):
    api = settings.GEMINI_API_KEY
    genai.configure(api_key=api)
    model = genai.GenerativeModel("gemini-2.0-flash")
    script = model.generate_content(
            f"For the given topic: {topic} "
            f"Generate a video script based on the following text: {extracted_text}. You can also use content from outside the text to explain. The video script should be in 1st person narrator explaining what the concept is without the use of any other person in the explanation unless needed explicitly. JUST GENERATE THE SCRIPT. DO NOT GENERATE ANY INTRODUCTION, EXPLANATION etc.",
        )
    return str(script)

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


# Notes Module

import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
import google.generativeai as genai
from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document as DocxDocument
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch

@require_POST
def generate_notes(request):
    topic_name = request.POST.get('subject-title')
    uploaded_file = request.FILES.get('file-upload')
    additional_notes = request.POST.get('additional-notes')
    website_link = request.POST.get('link-input') # Assuming the link input has this name

    extracted_text = ""

    if uploaded_file:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        try:
            if file_extension == '.pdf':
                extracted_text = pdf_extract_text(uploaded_file)
            elif file_extension == '.docx':
                doc = DocxDocument(uploaded_file)
                for paragraph in doc.paragraphs:
                    extracted_text += paragraph.text + "\n"
            # You can add support for other file types like .ppt or .txt if needed
        except Exception as e:
            return HttpResponse(f"Error processing file: {e}")

    all_inputs = f"Topic: {topic_name}\n\n"
    if extracted_text:
        all_inputs += f"Syllabus Content:\n{extracted_text}\n\n"
    if additional_notes:
        all_inputs += f"Additional Notes:\n{additional_notes}\n\n"
    if website_link:
        all_inputs += f"External Website Link: {website_link}\n\n"

    api_key = settings.GEMINI_API_KEY
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    try:
        response = model.generate_content(f"Generate comprehensive notes based on the following information:\n\n{all_inputs}")
        generated_notes = response.text
    except Exception as e:
        return HttpResponse(f"Error generating notes with Gemini: {e}")

    # Generate PDF
    notes_folder = 'notes_folder'
    os.makedirs(notes_folder, exist_ok=True)
    pdf_filename = f"{topic_name.replace(' ', '_')}_notes.pdf"
    pdf_filepath = os.path.join(notes_folder, pdf_filename)

    c = canvas.Canvas(pdf_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    line_height = 18
    y_position = 750  # Starting Y position

    for line in generated_notes.splitlines():
        p = Paragraph(line, normal_style)
        p_width, p_height = p.wrapOn(c, letter[0] - 2 * inch, line_height * 1.2) # Adjust width as needed
        if y_position - p_height < 50:  # Check for page bottom margin
            c.showPage()
            y_position = 750
        p.drawOn(c, inch, y_position - p_height)
        y_position -= p_height + 6  # Add some spacing

    c.save()

    return HttpResponse(f"Notes for '{topic_name}' generated successfully and saved as <a href='/download_notes/{pdf_filename}'>'{pdf_filename}'</a>")

def notes_page(request):
    return render(request, 'home/notes.html')

def download_notes(request, filename):
    file_path = os.path.join('notes_folder', filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return HttpResponse("File not found")