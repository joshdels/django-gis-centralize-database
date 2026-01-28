from rest_framework import serializers
from accounts.models import Profile
from gis_database.models import Project, File
from django.contrib.auth.models import User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["image", "first_name", "last_name", "location"]


class UserSerializer(serializers.ModelSerializer):
    """Used to serve the user's detail as an api"""

    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


class ProjectUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class ProjectSerializer(serializers.ModelSerializer):
    """Project's served in the api"""

    owner = ProjectUserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "owner",
            "name",
            "description",
            "created_at",
            "updated_at",
            "is_private",
        ]
        read_only_fields = ["id", "created_at", "owner"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["owner"] = request.user
        return super().create(validated_data)


class FileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = "__all__"

    def get_download_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(f"/api/files/{obj.id}/download/")
