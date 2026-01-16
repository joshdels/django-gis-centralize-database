# syntax=docker/dockerfile:1
# Use a specific version for stability (Debian Bookworm)
FROM python:3.12-slim-bookworm AS builder

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Install system dependencies (Build-time)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential python3-dev libpq-dev git curl nodejs npm \
        gdal-bin libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Virtual Env setup - Keep it in /opt/venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Cache Pip dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

# 4. Build Tailwind (NPM)
WORKDIR /app/theme/static_src
COPY theme/static_src/package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install
COPY theme/static_src/ ./ 
RUN npm run build

# --- Stage 2: Production runtime ---
FROM python:3.12-slim-bookworm

WORKDIR /app

# 6. Install Runtime-only GIS & Postgres libraries
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual env and code from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH="/opt/venv/bin:$PATH"
# FIX: Use wildcard for GDAL to handle version changes in slim images
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Scripted startup to ensure static files exist before Gunicorn starts
CMD sh -c "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput --clear && \
    gunicorn centralize_gis_db.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 2 \
      --timeout 60 \
      --max-requests 1000 \
      --log-level info \
"