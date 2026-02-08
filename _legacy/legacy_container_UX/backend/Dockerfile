# Use Python 3.11 slim image (matches pyproject.toml requirement)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (gcc for Python packages)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (backend only)
COPY src/ ./src/
COPY sdk/ ./sdk/
COPY static/ ./static/
COPY scripts/ ./scripts/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Expose port (Cloud Run will set PORT env var dynamically)
EXPOSE 8080

# Health check (increased start-period for cold starts)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Use exec form and shell to properly handle signals
# Add startup diagnostics before running app
CMD ["sh", "-c", "echo 'Starting app...' && python -c 'import sys; print(f\"Python {sys.version}\")' && python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level debug"]
