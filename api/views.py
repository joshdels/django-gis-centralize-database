from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import authenticate
from django.http import FileResponse, Http404
from django.db import transaction

from gis_database.models import Project, File
from .serializers import ProjectSerializer, UserSerializer, FileSerializer

from gis_database.utils import compute_hash

# -------------------- AUTHENTICATION --------------------


class LoginView(APIView):
    """
    ## POST /api/v1/login/

    Login endpoint for user authentication.

    **Request Body:**
    ```json
    {
        "username": "string",
        "password": "string"
    }
    ```

    **Responses:**
    - `200 OK` - Returns authentication token
      ```json
      { "token": "<auth_token>" }
      ```
    - `401 Unauthorized` - Invalid credentials
      ```json
      { "error": "Invalid credentials" }
      ```
    """

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
    """
    ## POST /api/v1/logout/

    Logs out the current authenticated user.

    Deletes the user's authentication token.

    **Responses:**
    - `200 OK`
      ```json
      { "success": "Logged out" }
      ```
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"success": "Logged out"})


class UserProfileView(APIView):
    """
    ## GET /api/v1/user-profile/

    Retrieve the currently authenticated user's profile.

    **Response:**
    ```json
    {
        "id": int,
        "username": "string",
        "email": "string",
        "profile": {
            "image": "string",
            "first_name": "string",
            "last_name": "string",
            "location": "string"
        }
    }
    ```
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# -------------------- PROJECT CRUD + VERSIONING --------------------


class ProjectViewSet(viewsets.ModelViewSet):
    """
    # Project API Endpoints

    Provides endpoints to manage projects and their file versions.

    ## Standard CRUD

    | Method | URL | Description |
    |--------|-----|-------------|
    | GET    | /projects/ | List projects of current user |
    | POST   | /projects/ | Create a new project |
    | GET    | /projects/{id}/ | Retrieve project details |
    | PUT/PATCH | /projects/{id}/ | Update project |
    | DELETE | /projects/{id}/ | Delete project |

    ## File Versioning

    | Method | URL | Description |
    |--------|-----|-------------|
    | POST   | /projects/{id}/files/upload/ | Upload a new file version |
    | GET    | /projects/{id}/files/ | List latest files |
    | GET    | /projects/{id}/versions/ | List all file versions |
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
        url_path="files/upload",
    )
    def upload_file(self, request, pk=None):
        """
        Upload a new file to a project with automatic versioning.

        **Behavior:**
        - If a file with the same hash exists → skip (200) and return existing file ID.
        - Otherwise → increments version number, marks as latest, stores hash.

        **Request Body:**
        - `file` (multipart file) – file to upload

        **Responses:**
        - `201 Created` – New file uploaded
        ```json
        {
            "id": int,
            "version": int,
            "hash": "string"
        }
        ```
        - `200 OK` – Duplicate file
        ```json
        {
            "detail": "File already exists",
            "file_id": int
        }
        ```
        - `400 Bad Request` – File not provided
        ```json
        { "error": "file required" }
        ```
        """
        project = self.get_object()
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            return Response({"error": "file required"}, status=400)

        file_hash = compute_hash(uploaded_file)
        existing = project.files.filter(hash=file_hash).first()

        if existing:
            return Response(
                {"detail": "File already exists", "file_id": existing.id}, status=200
            )

        # Versioning
        latest = (
            project.files.filter(name=uploaded_file.name).order_by("-version").first()
        )
        next_version = (latest.version + 1) if latest else 1

        with transaction.atomic():
            project.files.filter(name=uploaded_file.name).update(is_latest=False)

            new_file = File.objects.create(
                project=project,
                owner=request.user,
                file=uploaded_file,
                name=uploaded_file.name,
                version=next_version,
                hash=file_hash,
                is_latest=True,
            )

            return Response(
                {
                    "id": new_file.id,
                    "version": new_file.version,
                    "hash": new_file.hash,
                },
                status=201,
            )

    # -------------------- List Versions --------------------
    @action(
        detail=True,
        methods=["get"],
        url_path="files",
        permission_classes=[permissions.IsAuthenticated],
    )
    def list_files(self, request, pk=None):
        """
        List the latest files for a project.

        **Response:**
        ```json
        [
            {
                "id": int,
                "name": "string",
                "version": int,
                "hash": "string",
                "created_at": "datetime",
                "is_latest": bool,
                "download_url": "string"
            },
            ...
        ]
        ```
        """
        project = self.get_object()
        files = project.files.filter(is_latest=True)

        serializer = FileSerializer(files, many=True, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        url_path="versions",
        permission_classes=[permissions.IsAuthenticated],
    )
    def list_versions(self, request, pk=None):
        """
        List all file versions in a project.

        **Response:**
        ```json
        [
            {
                "file": "string",
                "version": int,
                "hash": "string",
                "created_at": "datetime",
                "is_latest": bool
            },
            ...
        ]
        ```
        """
        project = self.get_object()

        files = project.files.order_by("name", "-version")
        data = [
            {
                "file": f.name,
                "version": f.version,
                "hash": f.hash,
                "created_at": f.created_at,
                "is_latest": f.is_latest,
            }
            for f in files
        ]
        return Response(data)


class FileDownloadView(APIView):
    """
    ## GET /api/v1/files/<pk>/download/

    Download a file from a project.

    **Permissions:**
    - Only the project owner can download.

    **Responses:**
    - `200 OK` - Returns file attachment
    - `403 Forbidden` - User is not project owner
      ```json
      { "detail": "Forbidden" }
      ```
    - `404 Not Found` - File does not exist
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            file_obj = File.objects.select_related("project").get(pk=pk)
        except File.DoesNotExist:
            raise Http404

        if file_obj.project.owner != request.user:
            return Response({"detail": "Forbidden"}, status=403)

        return FileResponse(
            file_obj.file.open("rb"),
            as_attachment=True,
            filename=file_obj.name or file_obj.file.name,
        )
