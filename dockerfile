# --- Stage 1: Build ---
FROM python:3.12-slim-bookworm AS builder

# Standard environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (Legacy style - no --mount)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    git \
    curl \
    nodejs \
    npm \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Setup Virtual Env
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Pip dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Build Tailwind (NPM)
WORKDIR /app/theme/static_src
COPY theme/static_src/package*.json ./
RUN npm install
COPY theme/static_src/ ./ 
RUN npm run build

# --- Stage 2: Runtime ---
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install Runtime-only libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH="/opt/venv/bin:$PATH"
# Ensure GeoDjango can find the libraries
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Combined CMD for Migrations, Static Files, and Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && gunicorn centralize_gis_db.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]