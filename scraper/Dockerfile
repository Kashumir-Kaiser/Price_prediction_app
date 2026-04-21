# scraper/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY scraper/requirements.txt /app/scraper-requirements.txt
COPY backend/requirements.txt /app/backend-requirements.txt
RUN pip install --no-cache-dir -r /app/scraper-requirements.txt -r /app/backend-requirements.txt

# Build context is ./scraper — copy into /app/scraper so `scraper` is a package
# (COPY . /app/ would flatten files and break `python -m scraper.scheduler`).
COPY scraper/ /app/scraper/
COPY backend/ /app/backend/

ENV PYTHONPATH=/app

CMD ["python", "-m", "scraper.scheduler"]
