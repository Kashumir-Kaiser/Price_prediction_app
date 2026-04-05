# scraper/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire repo into /app so 'scraper' is a top-level importable package
COPY . /app/

# PYTHONPATH must include /app so 'from scraper.jobs...' resolves
ENV PYTHONPATH=/app

CMD ["python", "-m", "scraper.scheduler"]
