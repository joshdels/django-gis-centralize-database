# This will served as the central db for my GIS projects

This project serves as a centralized database and backend for multiple GIS projects.
It provides a unified storage layer for vector data and related GIS assets, with a Django-powered backend and spatial database support.

The backend runs on Django’s native server (for development) and can be exposed to serve public-facing GIS data and files.

---

**tech stack**
- Backend Hosting: Vultr
- Backend Framework: Django
- Database: PostgreSQL (vector / spatial data)
- Object Storage: Backblaze B2 (for files, exports, and large assets)

**Features**
- Centralized GIS data storage
- PostgreSQL-backed vector data management
- Object storage for large GIS files (e.g., GeoJSON, Shapefiles, exports)
- Django admin interface for data management
- calable backend for multiple GIS projects


**Intended Use**
- Acts as a shared backend for GIS tools (e.g., QGIS, QField, APIs)
- Central repository for spatial datasets
- Supports future integration with GeoDjango, PostGIS, and REST APIs

---

### Getting Stated
Set up environment
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
django-admin startproject centralize_gis_db .
```

run the backend
```
python manage.py runserver
```

----

For django commands
```
python manage.py makemigrations
python manage.py migrate
python manage.py shell
```

For Production
```
python manage.py collectstatic
```

------