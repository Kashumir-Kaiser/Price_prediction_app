# backend/Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Rust builder — compiles the market_features PyO3 extension
# ──────────────────────────────────────────────────────────────────────────────
FROM rust:1.77-slim AS rust-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev python3-pip libssl-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install maturin --break-system-packages

WORKDIR /rust
COPY rust/market_features/ .
RUN maturin build --release --out /wheels

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Python dependencies builder
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS py-builder

WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Install the Rust wheel built in stage 1
COPY --from=rust-builder /wheels/*.whl /wheels/
RUN pip install --prefix=/install /wheels/*.whl || echo "Rust wheel not found — Python fallback will be used"

# ──────────────────────────────────────────────────────────────────────────────
# Stage 3: Runtime
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=py-builder /install /usr/local

WORKDIR /app
COPY backend/app/ ./app/
COPY backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Mount point for the model cache volume
VOLUME ["/model-cache"]
ENV MODEL_CACHE_DIR=/model-cache

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

# ──────────────────────────────────────────────────────────────────────────────
# Stage 4: Test — overrides ENTRYPOINT with pytest
# ──────────────────────────────────────────────────────────────────────────────
FROM runtime AS test

# Install test-only packages that are NOT in production requirements.txt
RUN pip install --no-cache-dir \
    pytest>=8.1.0 \
    pytest-asyncio>=0.23.0 \
    pytest-cov>=5.0.0 \
    httpx>=0.27.0 \
    respx>=0.21.0 \
    factory-boy>=3.3.0

# Copy test files into the image
COPY backend/tests/ /app/tests/
COPY backend/pytest.ini /app/pytest.ini

# Override entrypoint — do NOT run entrypoint.sh (no DB migration, no uvicorn)
ENTRYPOINT ["python", "-m", "pytest"]
CMD ["tests/", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing"]
