from django import forms
from .models import Project

MAX_FILE_MB = 20


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "file"]
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file.size > MAX_FILE_MB * 1024 * 1024:
            raise forms.ValidationError(f"File too large. Max {MAX_FILE_MB} MB.")
        return file
