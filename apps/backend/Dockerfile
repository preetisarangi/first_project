# ==============================================================================
# Production Dockerfile for Autonomous Spec-to-Playwright Backend
# Platform: Render Free Web Service (python:3.11-slim + Node.js + Playwright)
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=10000 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 1. Install system utilities, curl, ca-certificates, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js LTS (v20.x) for Playwright test runner execution
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g npm@latest && \
    rm -rf /var/lib/apt/lists/*

# 3. Install Playwright CLI and Chromium browser with OS system dependencies
RUN npx playwright install --with-deps chromium

# 4. Copy backend dependencies and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy backend source code
COPY . .

# Expose Render port
EXPOSE 10000

# Health check instruction for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Launch FastAPI via Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]

