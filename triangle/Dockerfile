# Triangular Arbitrage Bot - API + Dashboard
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional): add as needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cache layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Ensure runtime dirs exist
RUN mkdir -p /app/data /app/logs

EXPOSE 8000

CMD ["uvicorn", "web.api:app", "--host", "0.0.0.0", "--port", "8000"]
