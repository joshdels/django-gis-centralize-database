# --- Stage 1: Build Python Virtual Env ---
FROM python:3.12-slim-bookworm AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Stage 2: Final Runtime ---
FROM python:3.12-slim-bookworm
WORKDIR /app

# Install GIS Libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python venv
COPY --from=python-builder /opt/venv /opt/venv

# Copy application code
COPY . .

ENV PATH="/opt/venv/bin:$PATH"
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Build Tailwind & collect static at container start
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py tailwind build && python manage.py collectstatic --noinput --clear && gunicorn centralize_gis_db.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
