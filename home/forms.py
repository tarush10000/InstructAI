# home/forms.py
from sqlite3 import IntegrityError
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
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    # Custom first name field with HTML attributes
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Team InstructAI',
            'id': 'name',
            'autocomplete': 'name'
        })
    )
    
    # Custom email field with HTML attributes
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'team@instructai.com',
            'id': 'email',
            'autocomplete': 'email'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'auth-input password-input',
            'placeholder': 'hello',
            'id': 'password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'auth-input password-input',
            'placeholder': 'Confirm Password',
            'id': 'password2',
            'autocomplete': 'new-password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set username to email and validate uniqueness
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name'].strip()
        
        if commit:
            try:
                user.save()
            except IntegrityError:
                raise ValidationError("A user with that email already exists.")
        return user
