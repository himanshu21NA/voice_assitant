# Backend Dockerfile for FastAPI + Playwright
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg libnss3 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libpango-1.0-0 \
    libcups2 libxshmfence1 libxfixes3 libxext6 libx11-6 libxtst6 libxss1 \
    libatk1.0-0 libdrm2 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright && playwright install

# Copy backend code
COPY . .

# Expose port
EXPOSE 10001

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10001"]
