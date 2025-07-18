# Multi-stage Dockerfile for Local Music Generator
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Build backend
FROM python:3.9-slim AS backend-builder

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Compile Python files
RUN python -m compileall .

# Stage 3: Production image
FROM python:3.9-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=backend-builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application
COPY --from=backend-builder /app/backend .

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static

# Create necessary directories
RUN mkdir -p /app/data/models /app/data/audio /app/logs /app/cache \
    && chown -R appuser:appuser /app

# Create configuration file
RUN cat > /app/config.py << 'EOF'
import os
from pathlib import Path

# Application settings
APP_NAME = os.getenv('APP_NAME', 'Local Music Generator')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Server settings
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Model settings
MODEL_NAME = os.getenv('MODEL_NAME', 'facebook/musicgen-small')
MODEL_CACHE_DIR = Path(os.getenv('MODEL_CACHE_DIR', '/app/data/models'))
AUTO_LOAD_MODEL = os.getenv('AUTO_LOAD_MODEL', 'true').lower() == 'true'
USE_GPU = os.getenv('USE_GPU', 'false').lower() == 'true'

# Audio settings
AUDIO_OUTPUT_DIR = Path(os.getenv('AUDIO_OUTPUT_DIR', '/app/data/audio'))
AUDIO_FORMAT = os.getenv('AUDIO_FORMAT', 'mp3')
AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '44100'))
AUDIO_QUALITY = os.getenv('AUDIO_QUALITY', 'high')

# Performance settings
MAX_MEMORY_MB = int(os.getenv('MAX_MEMORY_MB', '4096'))
MAX_GENERATION_TIME = int(os.getenv('MAX_GENERATION_TIME', '300'))
ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
CACHE_SIZE = int(os.getenv('CACHE_SIZE', '100'))

# Monitoring settings
ENABLE_MONITORING = os.getenv('ENABLE_MONITORING', 'true').lower() == 'true'
MONITORING_INTERVAL = float(os.getenv('MONITORING_INTERVAL', '1.0'))
RESOURCE_HISTORY_SIZE = int(os.getenv('RESOURCE_HISTORY_SIZE', '1000'))

# Security settings
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
ENABLE_CORS = os.getenv('ENABLE_CORS', 'true').lower() == 'true'
EOF

# Create health check script
RUN cat > /app/health_check.py << 'EOF'
#!/usr/bin/env python3
import sys
import requests
import time

def health_check():
    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("Health check passed")
                return 0
        except Exception as e:
            print(f"Health check failed (attempt {i+1}): {e}")
            if i < max_retries - 1:
                time.sleep(2)
    
    print("Health check failed after all retries")
    return 1

if __name__ == '__main__':
    sys.exit(health_check())
EOF

# Create startup script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create directories if they don't exist
mkdir -p /app/data/models /app/data/audio /app/logs /app/cache

# Check if model needs to be downloaded
if [ "$AUTO_LOAD_MODEL" = "true" ] && [ ! -d "/app/data/models/musicgen-small" ]; then
    log "Model not found, will be downloaded on first use"
fi

# Start the application
log "Starting Local Music Generator..."
log "Environment: ${ENVIRONMENT:-production}"
log "Debug mode: ${DEBUG:-false}"
log "GPU enabled: ${USE_GPU:-false}"

# Run the application
exec python main.py
EOF

# Make scripts executable
RUN chmod +x /app/entrypoint.sh /app/health_check.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/health_check.py

# Volume for persistent data
VOLUME ["/app/data", "/app/logs"]

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Metadata
LABEL maintainer="Local Music Generator Team" \
      version="1.0.0" \
      description="Local Music Generator using Facebook MusicGen" \
      org.opencontainers.image.title="Local Music Generator" \
      org.opencontainers.image.description="A local music generation application using Facebook MusicGen" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/yourusername/local-music-generator" \
      org.opencontainers.image.documentation="https://github.com/yourusername/local-music-generator/blob/main/README.md"