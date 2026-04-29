# backend/Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Rust builder — compiles the market_features PyO3 extension
# ──────────────────────────────────────────────────────────────────────────────
FROM rust:1.88-slim AS rust-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev python3-pip libssl-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install maturin --break-system-packages

ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
# Limit Rust parallelism to drastically reduce peak memory usage
ENV CARGO_BUILD_JOBS=1

WORKDIR /rust
COPY rust/market_features/ .

# Use --jobs 1 to override any maturin defaults
RUN maturin build --release --jobs 1 --out /wheels

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Python dependencies builder
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS py-builder

WORKDIR /build
COPY pyproject.toml ./pyproject.toml
COPY app/ ./app/
RUN pip install --no-cache-dir --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --timeout 1800 \
    --retries 5 \
    .

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
COPY app/ ./app/
COPY alembic.ini ./alembic.ini
COPY app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Ensure Python can find the app package
ENV PYTHONPATH=/app

# Default LSTM device (cpu, cuda, auto) – override in docker-compose if GPU is available
ENV DEVICE=cpu

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
COPY tests/ /app/tests/
COPY pytest.ini /app/pytest.ini

# Override entrypoint — do NOT run entrypoint.sh (no DB migration, no uvicorn)
ENTRYPOINT ["python", "-m", "pytest"]
# Enforce 60% coverage threshold as per update log
CMD ["tests/", "-v", "--tb=short", "--cov=app", "--cov-report=term-missing", "--cov-fail-under=60"]