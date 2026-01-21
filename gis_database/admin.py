from django.contrib import admin
from .models import Project, ProjectVersion

class ProjectVersionInline(admin.TabularInline):
    model = ProjectVersion
    extra = 0 

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user",)
    inlines = [ProjectVersionInline]
