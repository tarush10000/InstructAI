# home/forms.py
from django import forms
import os

class VideoGenerationForm(forms.Form):
    topic = forms.CharField(max_length=200, label='Video Topic')
    files = forms.FileField(widget=forms.FileInput(), label='Upload Files (PDF, PPT, DOC)')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_files(self):
        file = self.request.FILES.get('files')
        if not file:
            raise forms.ValidationError("Please upload a file.")
        allowed_extensions = ['.pdf', '.ppt', '.pptx', '.doc', '.docx']
        name, ext = os.path.splitext(file.name)
        if ext.lower() not in allowed_extensions:
            raise forms.ValidationError(f"File type not supported: {file.name}. Allowed types are: PDF, PPT, DOC.")
        return file