from django import forms
from .models import Project, ProjectFile

class ProjectForm(forms.ModelForm):
    initial_file = forms.FileField(required=False, help_text="Optional initial file upload")

    class Meta:
        model = Project
        fields = ["name", "description"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.instance and self.user:
            self.instance.user = self.user

    def save(self, commit=True):
        project = super().save(commit=commit)
        uploaded_file = self.cleaned_data.get("initial_file")
        if uploaded_file:
            ProjectFile.objects.create(project=project, file=uploaded_file)
        return project



class ProjectFileUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectFile
        fields = ["file"]

    def save(self, commit=True):
        project_file = super().save(commit=False)
        new_file = self.cleaned_data.get("file")
        if new_file:
            project_file.create_new_version(new_file)
        if commit:
            project_file.save()
        return project_file