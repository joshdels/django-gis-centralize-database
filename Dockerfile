# ==============================
# Stage 1: Build Tailwind frontend
# ==============================
FROM node:20-slim AS frontend-builder
WORKDIR /app/theme/static_src

# 1. Copy package files first for caching
# COPY theme/static_src/package*.json ./theme/static_src/
# RUN cd theme/static_src && npm install
COPY theme/static_src/package*.json ./
RUN npm install

# 2. Copy templates & frontend source (Tailwind needs HTML to scan)
COPY src ./src
COPY gis_database ./gis_database
COPY theme ./theme

# 3. Build Tailwind CSS
RUN npm run build

# ==============================
# Stage 2: Build Python virtual environment
# ==============================
FROM python:3.12-slim-bookworm AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ==============================
# Stage 3: Final Runtime
# ==============================
FROM python:3.12-slim-bookworm
WORKDIR /app

# Install GIS libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python virtual environment
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy built Tailwind static files
# COPY --from=frontend-builder /app/theme/static /app/theme/static
COPY --from=frontend-builder /app/theme/static_src/static/css/dist /app/theme/static

# Copy Django code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Expose port
EXPOSE 8000

# CMD: migrate, collectstatic, run gunicorn
CMD ["sh", "-c", "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput --clear && \
    gunicorn centralize_gis_db.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    "]
