import os
import json
import numpy as np
import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry, GeometryCollection
from ..models import SpatialData

def process_spatial_file(file_instance):
    valid_extensions = [".geojson", ".gpkg", ".kml"]
    extension = os.path.splitext(file_instance.file.name)[1].lower()

    if extension not in valid_extensions:
        print(f"Skipping non-spatial file: {file_instance.name}")
        return

    # Use 'with' to ensure the file is closed after reading
    with file_instance.file.open(mode="rb") as f:
        gdf = gpd.read_file(f)

    # Convert NaNs to None to avoid JSON errors later
    gdf = gdf.replace({np.nan: None})

    # Ensure CRS is WGS84
    current_epsg = gdf.crs.to_epsg() if gdf.crs else None
    if current_epsg != 4326:
        gdf = gdf.to_crs(epsg=4326)

    geoms = []
    all_properties = []

    for _, row in gdf.iterrows():
        # row.geometry.wkb is bytes; .hex() converts it to a clean string
        if row.geometry:
            django_geom = GEOSGeometry(row.geometry.wkb.hex(), srid=4326)
            geoms.append(django_geom)

            prop = row.drop("geometry").to_dict()
            all_properties.append(json.loads(json.dumps(prop, default=str)))

    if geoms:
        collection = GeometryCollection(geoms, srid=4326)

        SpatialData.objects.create(
            project=file_instance.project,
            source_file=file_instance,
            geometry=collection,
            properties=all_properties,
        )
        print(f"Successfully ingested collection for {file_instance.name}")