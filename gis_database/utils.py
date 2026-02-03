import hashlib
import io
import zipfile

from django.core.files.base import ContentFile


def compute_hash(uploaded_file):
    uploaded_file.seek(0)
    hasher = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        hasher.update(chunk)
    uploaded_file.seek(0)
    return hasher.hexdigest()


def create_empty_qgz(project_name):
    """Return a BytesIO object of a valid empty QGIS project as .qgz"""
    qgs_content = f"""<qgis projectname="{project_name}" version="3.40"><title>{project_name}</title></qgis>"""

    qgz_bytes = io.BytesIO()
    with zipfile.ZipFile(qgz_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{project_name}.qgs", qgs_content)

    qgz_bytes.seek(0)
    qgz_bytes.name = f"{project_name}.qgz"
    return qgz_bytes


def create_project_file(project, owner=None):
    """Create the inial empty QGZ file for the project"""

    if project.files.exists():
        return None

    from .models import File

    owner = owner or project.owner
    qgz_bytes = create_empty_qgz(project.name)

    content_file = ContentFile(qgz_bytes.getvalue(), name=qgz_bytes.name)

    file_obj = File(
        project=project,
        owner=owner,
        name=f"{project.name}.qgz",
        version=1,
        is_latest=True,
    )

    file_obj.file.save(content_file.name, content_file, save=False)
    file_obj.hash = compute_hash(file_obj.file)
    file_obj.save()
    return file_obj
