import hashlib
import io
import json
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


def serialize_spatial_data(spatial_record):
    """
    Safely serializes a spatial record into a GeoJSON FeatureCollection.
    Handles NoneType records and missing/malformed properties.
    """
    # 1. Guard against NoneType records (Fixes your current crash)
    if not spatial_record or not hasattr(spatial_record, "geometry"):
        return {"type": "FeatureCollection", "features": []}

    try:
        # Use the .geojson property from GeoDjango/PostGIS
        geojson_geom = json.loads(spatial_record.geometry.geojson)
    except (AttributeError, ValueError, TypeError):
        # Fallback if geometry is empty or invalid
        return {"type": "FeatureCollection", "features": []}

    # Ensure properties is at least an empty dict to avoid 'NoneType' errors later
    record_properties = spatial_record.properties or {}
    features = []

    # Case A: Single geometry (Point, LineString, Polygon, etc.)
    if geojson_geom.get("type") != "GeometryCollection":
        features.append(
            {
                "type": "Feature",
                "geometry": geojson_geom,
                "properties": record_properties,
            }
        )

    # Case B: GeometryCollection
    else:
        geometries = geojson_geom.get("geometries", [])
        prop_list = record_properties.get("features", [])

        for i, geom in enumerate(geometries):
            props = {}
            if isinstance(prop_list, list) and i < len(prop_list):
                props = prop_list[i]

            features.append({"type": "Feature", "geometry": geom, "properties": props})

    return {"type": "FeatureCollection", "features": features}
