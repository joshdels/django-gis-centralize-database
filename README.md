# This will served as the central db for my GIS projects

This project serves as a centralized database and backend for multiple GIS projects.
It provides a unified storage layer for vector data and related GIS assets, with a Django-powered backend and spatial database support.

The backend runs on Django’s native server (for development) and can be exposed to serve public-facing GIS data and files.


**tech stack**
- UI: Django-Tailwind -> https://django-tailwind.readthedocs.io/en/latest/installation.html
- Auth: Django AllAuth -> https://docs.allauth.org/en/latest/account/configuration.html
- Backend Framework: Django
- Backend Hosting: Vultr
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

#### ENV SETTINGS
For Development
```
touch .env.dev
```

**file .env.dev structure**
DJANGO_ENV=env
PROJECT_KEY= 'YOUR_DJANGO_KEY"
ALLOWED_HOSTS=localhost,127.0.0.1
DEUBG=True
EMAIL_BACKEND=console


then run
```
export DJANGO_ENV=dev
python manage.py runserver
```


For Production
```
touch .env.prod
```

**file .env.prod structure**
DJANGO_ENV=prod
PROJECT_KEY= 'YOUR_DJANGO_KEY"
ALLOWED_HOSTS=localhost,127.0.0.1
DEUBG=True
EMAIL_BACKEND=console


```
python manage.py collectstatic
export DJANGO_ENV=prod
gunicorn centralize_gis_db.wsgi:application
```

------