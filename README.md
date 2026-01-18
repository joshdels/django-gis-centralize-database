# This will served as the central db for my GIS projects

This project serves as a centralized database and backend for multiple GIS projects.
It provides a unified storage layer for vector data and related GIS assets, with a Django-powered backend and spatial database support.

The backend runs on Django’s native server (for development) and can be exposed to serve public-facing GIS data and files.

**tech stack**

- UI: Django-Tailwind -> https://django-tailwind.readthedocs.io/en/latest/installation.html
- UI Styling: DaisyUI -> https://daisyui.com/
- Auth: Django AllAuth -> https://docs.allauth.org/en/latest/account/configuration.html
- Backend Framework: Django
- Backend Hosting: Vultr
- Database (Vultr): PostgreSQL (vector / spatial data)
- Object Storage: Backblaze B2 (for files, exports, and large assets)
- Email: Brevo

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

---

For django commands

```
python manage.py makemigrations
python manage.py migrate
python manage.py shell
```

#### CONFIGURATION

Development Environment (.env.dev)
Create a file named .env.dev for local testing:

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

Production Environment (.env.prod)
Create a file named .env.prod for the Vultr VM:

```
touch .env.prod
```

**file .env.prod structure**
DJANGO_ENV=prod PROJECT_KEY=your_production_key
ALLOWED_HOSTS=your_domain.com,your_vultr_ip
DEBUG=False
DB_NAME=your_db
DB_USER=user
DB_PASSWORD=your_password
DB_HOST=your_db_vm_private_ip
DB_PORT=port
B2_APP_KEY_ID=your_id
B2_APP_KEY=your_key
B2_BUCKET_NAME=your_bucket

---

#### Deployment Commands

Database Migrations

```
python manage.py collectstatic
export DJANGO_ENV=prod
gunicorn centralize_gis_db.wsgi:application
```

---

### Tailwind Config

```
python manage.py tailwind init
python manage.py tailwind start
```

---

### Remote Postgres Instruction

this connects to the virtual machine and docker hosted a postgres/postgis image
on your virtual machine, copy the docker-postgis.yml
it should have

```
DB_NAME="YOUR_DB_NAME"
DB_USER="USER"
DB_PASSWORD="PASSWORD"
```

### For dockerize Django

use the .env.prod for deployment

```
docker-compose up -d  # to run
docker ps             # to check
docker-compose down   # to stop
docker exect -it CONTAINER_NAME bash # to perform inside the container
```

---

### CI/CD Pipelines

used for deploying apps and adding features continuously

1. Create a deploy.yml file in .github/workflows
2. save the following keys in the secret github actions

```
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="YOUR_USERNAME"
SSH_PRIVATE_KEY="YOUR_SERVER_KEY_GENERATED
```

for generating server keys write this on the server cli

```
# FOR GITHUB CI/CD keys
Authorize keys inside the server
cat ~/github-action-new.3pub >> ~/.ssh/authorized_keys
cat ~/github-action-new  #then copy this to your github action secret key env

rm ~/github-action-new ~/github-action-new.pub # optional
```
