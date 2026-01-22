from rest_framework import serializers
from gis_database.models import Project
from django.contrib.auth.models import User
from accounts.models import Profile


class ProjectSerializer(serializers.ModelSerializer):
    """Project's served in the api"""
    class Meta:
        model = Project
        fields = ["id", "user", "name", "description", "file", "created_at", "updated_at", "is_private"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["user"] = request.user
        return super().create(validated_data)
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['image', 'first_name', 'last_name', 'location']

class UserSerializer(serializers.ModelSerializer):
    """Used to serve the user's detail as an api"""
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']