from django.contrib import admin
from .models import Project, File, FileActivity


# Inline for Files under a Project
class FileInline(admin.TabularInline):
    model = File
    extra = 0
    readonly_fields = ("version", "hash", "is_latest", "created_at")
    fields = ("name", "file_folder", "file", "version", "hash", "is_latest", "created_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_deleted", "is_private", "created_at")
    search_fields = ("name", "owner__username")
    list_filter = ("is_deleted", "is_private", "created_at")
    inlines = [FileInline]


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ("project", "name", "version", "is_latest", "created_at")
    search_fields = ("name", "project__name", "owner__username")
    list_filter = ("is_latest", "created_at", "project")


@admin.register(FileActivity)
class FileActivityAdmin(admin.ModelAdmin):
    list_display = ("file", "owner", "action", "created_at")
    search_fields = ("file__name", "owner__username", "action")
    list_filter = ("action", "created_at")
