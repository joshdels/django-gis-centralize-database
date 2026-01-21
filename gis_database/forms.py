from django import forms
from .models import Project, ProjectVersion


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "file", "description"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.instance and self.user:
            self.instance.user = self.user


class ProjectVersionForm(forms.ModelForm):
    class Meta:
        model = ProjectVersion
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(
                attrs={"class": "file-input file-input-bordered w-full"}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True
