FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install GDAL, GEOS, and other system libraries required by rasterio
# Also install curl for health-check probing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    g++ \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL include paths so pip can compile rasterio against the system GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase only (keep image lean)
COPY backend ./backend

EXPOSE 8000

# Bind to 0.0.0.0 and dynamically respect the $PORT environment variable supplied by Render
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
