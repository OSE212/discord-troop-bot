FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    WEB_PORT=8080 \
    WEB_HOST=0.0.0.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY bot/ ./bot/
COPY config/ ./config/
COPY run.py web_run.py ./

# Expose web panel port
EXPOSE 8080

# Run bot + web panel (run.py starts both by default)
CMD ["python", "run.py"]
