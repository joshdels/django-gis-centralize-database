from django.contrib import admin
from .models import Project, ProjectFile, ProjectFileVersion


# --- Inline for ProjectFile ---
class ProjectFileInline(admin.TabularInline):
    model = ProjectFile
    extra = 0
    


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "archived", "is_private", "to_trash", "created_at")
    inlines = [ProjectFileInline]


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ("project", "file", "created_at")


@admin.register(ProjectFileVersion)
class ProjectFileVersionAdmin(admin.ModelAdmin):
    list_display = ("project_file", "version_number", "created_at", "synced")
    readonly_fields = ("version_number", "created_at", "synced", "checksum", "remote_path", "synced_at")
