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


import json

def serialize_spatial_data(spatial_record):
    """
    Safely serializes a spatial record into a GeoJSON FeatureCollection.
    Handles NoneType records and missing/malformed properties.
    """
    # 1. Guard against NoneType records
    if not spatial_record or not hasattr(spatial_record, "geometry"):
        return {"type": "FeatureCollection", "features": []}

    try:
        # Use the .geojson property from GeoDjango/PostGIS
        geojson_geom = json.loads(spatial_record.geometry.geojson)
    except (AttributeError, ValueError, TypeError):
        return {"type": "FeatureCollection", "features": []}

    # 2. Safely handle properties (could be a list or a dict)
    record_properties = spatial_record.properties or {}
    features = []

    # Case A: Single geometry (Point, LineString, Polygon, etc.)
    if geojson_geom.get("type") != "GeometryCollection":
        features.append({
            "type": "Feature",
            "geometry": geojson_geom,
            "properties": record_properties,
        })

    # Case B: GeometryCollection
    else:
        geometries = geojson_geom.get("geometries", [])
        
        # FIX: Check if properties is a dict or a list
        if isinstance(record_properties, dict):
            # If it's a dict, try to find a "features" key inside
            prop_list = record_properties.get("features", [])
        else:
            # If it's already a list, use it directly
            prop_list = record_properties

        for i, geom in enumerate(geometries):
            props = {}
            # Match the geometry to its corresponding property index
            if isinstance(prop_list, list) and i < len(prop_list):
                props = prop_list[i]
            elif isinstance(prop_list, dict):
                props = prop_list # Fallback if there's only one dict for many geoms

            features.append({
                "type": "Feature", 
                "geometry": geom, 
                "properties": props
            })

    return {"type": "FeatureCollection", "features": features}