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
    qgs_content = f"""<qgis projectname="{project_name}" version="3.34"><title>{project_name}</title></qgis>"""
    
    qgz_bytes = io.BytesIO()
    with zipfile.ZipFile(qgz_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{project_name}.qgs", qgs_content)
    
    qgz_bytes.seek(0)
    qgz_bytes.name = f"{project_name}.qgz"
    return qgz_bytes