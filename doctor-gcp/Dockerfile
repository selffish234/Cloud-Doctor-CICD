# Cloud Doctor - Enhanced Doctor Zone Dockerfile
# GCP Cloud Run deployment with Gemini + Claude AI

FROM python:3.11-slim

# Metadata
LABEL maintainer="Cloud Doctor MVP"
LABEL description="Hybrid Cloud Monitoring with AI-powered Diagnosis and Terraform Generation"
LABEL gcp.service="Cloud Run"

# Working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Layer caching optimization
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
# Use wildcard to include all Python files (main.py imports log_analyzer_vertex)
COPY *.py .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Python unbuffered mode
ENV PYTHONUNBUFFERED=1

# Cloud Run provides PORT via environment variable (default 8080)
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run FastAPI server
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1
