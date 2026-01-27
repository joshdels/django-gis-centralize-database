from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.utils import timezone

from gis_database.models import Project
from .serializers import ProjectSerializer, UserSerializer


# -------------------- AUTHENTICATION --------------------


class LoginView(APIView):
    """Login endpoint: returns token if credentials are correct."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """Logout endpoint: deletes the user's token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"success": "Logged out"})


# -------------------- PROJECT CRUD + VERSIONING --------------------


class ProjectViewSet(viewsets.ModelViewSet):
    """
    Project API ViewSet

    - Standard CRUD: list, retrieve, create, update, destroy
    - Versioning endpoints:
        - POST /projects/{id}/upload-version/  -> add a new version
        - GET  /projects/{id}/versions/       -> list all versions
    """

    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only return projects for the authenticated user."""
        return Project.objects.filter(owner=self.request.user)

    # -------------------- Version Upload --------------------
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        url_path="upload-version",
        permission_classes=[permissions.IsAuthenticated],
    )
    def upload_version(self, request, pk=None):
        """
        Upload a new file version for this project.

        Request:
            - file (multipart/form-data): the new file

        Response:
            - version: new version number
            - filename: file path
            - uploaded_at: timestamp
        """
        project = self.get_object()
        new_file = request.FILES.get("file")

        if not new_file:
            return Response(
                {"error": "File is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_version = project.create_new_version(new_file)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "version": new_version.version_number,
                "filename": new_version.file.name,
                "uploaded_at": new_version.created_at,
            },
            status=status.HTTP_201_CREATED,
        )

    # -------------------- List Versions --------------------
    @action(
        detail=True,
        methods=["get"],
        url_path="versions",
        permission_classes=[permissions.IsAuthenticated],
    )
    def list_versions(self, request, pk=None):
        """
        List all versions for a project.

        Response:
            - versions: list of version_number, filename, created_at
        """
        project = self.get_object()
        versions = project.versions.all()
        data = [
            {
                "version": v.version_number,
                "filename": v.file.name,
                "created_at": v.created_at,
            }
            for v in versions
        ]
        return Response(data)


# -------------------- USER PROFILE --------------------


class UserProfileView(APIView):
    """Return the currently authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
