# --- Stage 1: Build ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies (Build-time)
RUN apt-get update && \
    apt-get install -y \
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

# 1. Create a virtual environment and use it for all subsequent pip commands
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files and build Tailwind
COPY . .
WORKDIR /app/theme/static_src
RUN npm install && npm run build
WORKDIR /app

# --- Stage 2: Production runtime ---
FROM python:3.12-slim

WORKDIR /app

# Install ONLY runtime GIS and Postgres libraries
RUN apt-get update && \
    apt-get install -y \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

# 3. Copy the application code (including the built Tailwind assets)
COPY --from=builder /app /app

# 4. Set environment variables so the system uses the venv
ENV PATH="/opt/venv/bin:$PATH"
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# 5. ing the full path for Gunicorn ensures it starts correctly
CMD sh -c "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn centralize_gis_db.wsgi:application --bind 0.0.0.0:8000 --workers 4 --access-logfile - --error-logfile - \
"