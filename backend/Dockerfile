FROM python:3.12-slim

WORKDIR /app

# Install build tools needed by cryptography wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy package definition and source first (better layer caching)
COPY pyproject.toml .
COPY src/ src/

# Install package + runtime dependencies
RUN pip install --no-cache-dir -e .

# Copy API module
COPY api/ api/

# Create a non-root user and drop privileges
RUN adduser --disabled-password --no-create-home --gecos "" appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
