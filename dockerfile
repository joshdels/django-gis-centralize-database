# syntax=docker/dockerfile:1
# --- Stage 1: Build ---
FROM python:3.12-slim AS builder

WORKDIR /app

# 1. Install system dependencies first (These change almost never)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential python3-dev libpq-dev git curl nodejs npm \
        gdal-bin libgdal-dev libgeos-dev libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Virtual Env setup
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Cache Pip dependencies (Only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install -r requirements.txt

# 4. Cache NPM dependencies (Only re-runs if package.json changes)
# We move into the theme folder BEFORE copying the whole project
WORKDIR /app/theme/static_src
COPY theme/static_src/package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm install

# 5. Copy the rest of the project and build Tailwind
WORKDIR /app
COPY . .
WORKDIR /app/theme/static_src
RUN npm run build
WORKDIR /app

# --- Stage 2: Production runtime ---
FROM python:3.12-slim

WORKDIR /app

# 6. Install ONLY runtime libraries (Minimal)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        gdal-bin libgdal-dev libgeos-dev libproj-dev libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH="/opt/venv/bin:$PATH"
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Use 2 workers as we discussed to prevent the '3-minute hang'
CMD sh -c "\
    python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput && \
    gunicorn centralize_gis_db.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 2 \
      --timeout 30 \
      --max-requests 1000 \
"