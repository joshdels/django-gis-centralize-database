# --- Stage 1: Build Frontend (Tailwind) ---
# We use a dedicated Node image so we don't have to 'apt-get install npm'
FROM node:20-slim AS frontend-builder
WORKDIR /app/theme/static_src
COPY theme/static_src/package*.json ./
# Docker will cache this unless package.json changes
RUN npm install
COPY theme/static_src/ ./
RUN npm run build

# --- Stage 2: Build Python Virtual Env ---
FROM python:3.12-slim-bookworm AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Install only what's needed for pip (no GIS here to keep this stage light)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Stage 3: Final Runtime ---
FROM python:3.12-slim-bookworm
WORKDIR /app

# 1. Install GIS Libraries (Stable - rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy the Python environment from python-builder
COPY --from=python-builder /opt/venv /opt/venv
# 3. Copy the compiled Tailwind CSS from frontend-builder
COPY --from=frontend-builder /app/theme/static /app/theme/static
# 4. Copy your actual code (Last - changes most frequently)
COPY . .

ENV PATH="/opt/venv/bin:$PATH"
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && gunicorn centralize_gis_db.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]