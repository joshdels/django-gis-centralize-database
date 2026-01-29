# ==============================
# Python Runtime for Django + Tailwind Standalone
# ==============================
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies (GIS libs, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy Django project
COPY . .

# Environment variables
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Expose port
EXPOSE 8000

# CMD: migrate, build Tailwind, collectstatic, then run Gunicorn
CMD ["sh", "-c", "\
    python manage.py migrate --noinput && \
    python manage.py tailwind build && \
    python manage.py collectstatic --noinput --clear && \
    gunicorn centralize_gis_db.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
"]
