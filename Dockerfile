# Multi-stage / Production Dockerfile for Antigravity Universal Hub
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install system dependencies (ffmpeg for whisper audio, git, curl, tar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ffmpeg \
    tar \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Antigravity CLI (agy)
RUN curl -fsSL https://antigravity.google/cli/install.sh | bash || true

# Add agy to PATH
ENV PATH="/root/.local/bin:/root/.agy/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY run.py .
COPY miniapp_web.tar.gz .

# Unpack Flutter Web Mini App if archive is present
RUN mkdir -p frontend_flutter/build && \
    tar -xzf miniapp_web.tar.gz -C frontend_flutter/build && \
    rm -f miniapp_web.tar.gz

# Create directories for persistent data
RUN mkdir -p data .agy_uploads

EXPOSE 8000

# Run both Telegram Bot and FastAPI Server concurrently
CMD ["python", "run.py"]
