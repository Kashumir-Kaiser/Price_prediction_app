# backend/Dockerfile
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /install /usr/local

WORKDIR /app
COPY app/ ./app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# CRITICAL: No model download here. Models loaded at runtime via entrypoint

# Mount point for the model cache volume
VOLUME ["/model-cache"]
ENV MODEL_CACHE_DIR=/model-cache

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
