from django.contrib import admin
from .models import Profile

admin.site.register(Profile)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

# This puts Profile fields at the bottom of the User page
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Replace the default User admin with our merged one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)