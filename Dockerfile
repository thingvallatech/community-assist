# Community Assist - Full Dockerfile
# Includes scraping dependencies (Playwright, PDF processing, NLP)

FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    wget \
    gnupg \
    # For Playwright
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    # For PDF processing (camelot/ghostscript)
    ghostscript \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spacy English model
RUN python -m spacy download en_core_web_sm

# Install Playwright browsers as appuser
USER appuser
RUN playwright install chromium
USER root

# Copy application code
COPY --chown=appuser:appuser . .

# Make scripts executable
RUN chmod +x docker-entrypoint.sh run.sh 2>/dev/null || true

# Switch to non-root user
USER appuser

# Default command (can be overridden)
CMD ["python", "-m", "src.main"]
