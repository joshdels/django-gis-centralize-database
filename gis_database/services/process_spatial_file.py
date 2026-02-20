import os
import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry
from ..models import GeoFeature
import numpy as np
import json


def process_spatial_file(file_instance):
    valid_extensions = [".geojson", ".gpkg", ".kml"]
    extension = os.path.splitext(file_instance.file.name)[1].lower()

    if extension not in valid_extensions:
        print(f"Skipping non-spatial file: {file_instance.name}")
        return

    with file_instance.file.open(mode="rb") as f:
        gdf = gpd.read_file(f)

    gdf = gdf.replace({np.nan: None})

    current_epsg = gdf.crs.to_epsg() if gdf.crs else None
    if current_epsg != 4326:
        gdf = gdf.to_crs(epsg=4326)

    features = []
    for _, row in gdf.iterrows():
        django_geom = GEOSGeometry(row.geometry.wkt, srid=4326)

        properties = row.drop("geometry").to_dict()
        properties_json = json.loads(json.dumps(properties, default=str))

        features.append(
            GeoFeature(
                project=file_instance.project,
                source_file=file_instance,
                geometry=django_geom,
                properties=properties_json,
            )
        )

    if features:
        GeoFeature.objects.bulk_create(features)
        print(f"Successfully ingested {len(features)} features.")
