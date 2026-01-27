# --- Stage 1: Build Frontend (Tailwind v4) ---
FROM node:20-slim AS frontend-builder
WORKDIR /app

# 1. Copy package files first for better caching
COPY theme/static_src/package*.json ./theme/static_src/
RUN cd theme/static_src && npm install

# 2. !!! FIX FOR TAILWIND v4 !!!
# Copy the folders containing your HTML templates. 
# Without these, Tailwind v4 scans "nothing" and deletes all your CSS classes.
COPY gis_database/ ./gis_database/
COPY theme/ ./theme/

# 3. Run the build from the static_src directory
WORKDIR /app/theme/static_src
RUN npm run build

# --- Stage 2: Build Python Virtual Env (No Changes) ---
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

# --- Stage 3: Final Runtime ---
FROM python:3.12-slim-bookworm
WORKDIR /app

# 1. Install GIS Libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy the Python environment
COPY --from=python-builder /opt/venv /opt/venv

# 3. !!! FIX FOR MISSING CSS !!!
# Copy the built static folder. 
# Tailwind v4 usually outputs to theme/static/dist/styles.css
COPY --from=frontend-builder /app/theme/static /app/theme/static

# 4. Copy your actual code
COPY . .

ENV PATH="/opt/venv/bin:$PATH"
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# CMD stays the same
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && gunicorn centralize_gis_db.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]