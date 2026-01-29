# ==============================
# Stage 1: Build Tailwind (Node)
# ==============================
FROM node:20-slim AS frontend-builder
WORKDIR /app/theme/static_src

COPY theme/static_src/package*.json ./
RUN npm install

COPY theme/static_src/src ./src
COPY theme/templates ../templates
COPY gis_database ../gis_database

RUN npm run build


# ==============================
# Stage 2: Python Builder
# ==============================
FROM python:3.12-slim-bookworm AS python-builder
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt


# ==============================
# Stage 3: Final Runtime
# ==============================
FROM python:3.12-slim-bookworm
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Django app FIRST
COPY . .

# Create static directory
RUN mkdir -p /app/static

# Copy compiled Tailwind CSS LAST (prevents overwriting)
COPY --from=frontend-builder /app/theme/static/css/dist \
    /app/theme/static/css/dist

ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

EXPOSE 8000

CMD ["sh", "-c", "\
    mkdir -p /app/staticfiles && \
    python manage.py collectstatic --noinput --clear && \
    python manage.py migrate --noinput && \
    gunicorn centralize_gis_db.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 60 \
    "]