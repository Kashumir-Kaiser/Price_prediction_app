# Market Analysis Platform

A full-stack financial market analysis platform built with Python (FastAPI), TypeScript (React), Go, and Rust. Supports both US crypto markets (via Alpaca) and Vietnamese stock markets (via vnstock3).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    Client (Browser)                                 │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ HTTPS / localhost:3000
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              Nginx Reverse Proxy (Port 80)                         │
│                                   Serves static assets                             │
│                                   Proxies /api/* to backend                        │
└──────────────────────────────────────┬─────────────────────────────────────────────┘
                                       │
          ┌────────────────────────────┼─────────────────────────┐
          │                            │                         │
          ▼                            ▼                         │
┌──────────────────┐        ┌──────────────────┐                 │
│   React SPA      │        │   FastAPI        │                 │
│   (Nginx static) │        │   Backend        │                 │
│   Port 3000      │        │   Port 8000      │                 │
└──────────────────┘        └────────┬─────────┘                 │
                                     │                           │
                                     │ PostgreSQL (asyncpg)      │ 
                                     │ Redis (aioredis)          │
                                     │ Model Cache Volume        │
                                     │                           │
                          ┌──────────┴──────────┐                │
                          │                     │                │
                          ▼                     ▼                │
               ┌──────────────────┐   ┌──────────────────┐       │
               │   PostgreSQL 16  │   │     Redis 7      │       │
               │   (Market Data)  │   │   (Cache/Rate)   │       │
               └──────────────────┘   └──────────────────┘       │
                          ▲                                      │
                          │                                      │
               ┌──────────┘                                      │
               │                                                 │
               ▼                                                 │
     ┌──────────────────┐                                        │
     │  Go Scraper      │                                        │
     │  (Cron Jobs)     │                                        │
     │  Alpaca / VNStock│                                        │
     └──────────────────┘                                        │
               │                                                 │
               └─────────────────────────────────────────────────┘
```

## Features

### Data Sources
- **Alpaca Markets API**: Crypto (BTC/USD, ETH/USD, SOL/USD) and stablecoins (USDT/USD, USDC/USD)
- **vnstock**: Vietnamese stocks (VNM, VIC, FPT, SSI, etc.) with financial reports

### Machine Learning Models
- **Random Forest**: Classical ensemble model for direction prediction
- **XGBoost**: Gradient boosting classifier
- **LSTM**: PyTorch-based recurrent neural network

### API Endpoints
- `GET /api/health` - Health check
- `GET /api/prices/crypto/latest` - Latest crypto prices
- `GET /api/prices/crypto/history` - Historical crypto OHLCV
- `GET /api/prices/stocks/history` - Historical stock OHLCV
- `GET /api/prices/stocks/financials` - Financial reports
- `GET /api/predictions/crypto` - Crypto price predictions
- `GET /api/predictions/stock` - Stock price predictions
- `POST /api/predictions/retrain` - Trigger model retraining

## Quick Start

### Prerequisites
- Docker & Docker Compose (with Compose Watch plugin)
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Go 1.22+ (for scraper development)
- Rust 1.77+ (for building the native extension)

### Environment Setup

```bash
# 1. Clone and enter the repository
cd market-analysis-platform

# 2. Copy the example environment file
cp .env.example .env
# Edit .env with your actual API keys (Alpaca, etc.)

# 3. Build and start everything (production mode)
docker compose up -d --build

# 4. Or start in development mode with live reload
docker compose up --watch
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Nginx (combined): http://localhost:8081

### Normal Boot
```bash
# Build and start all application services (no tests)
docker compose up -d --build
```

### Run Only Tests
Tests are isolated in a separate Compose file (docker-compose.test.yml).
Run all test containers and exit:

```bash
# Run all test containers and exit
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit backend-test frontend-test scraper-test
```

To run only one test service:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend-test
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + TypeScript + Tailwind CSS | SPA with real-time charts |
| Backend API | FastAPI + SQLAlchemy (async) + PostgreSQL | REST API, auth, ML inference |
| ML Feature Engineering | Rust + PyO3 + Polars | 20-40x faster RSI/MACD/Bollinger |
| Data Scraper | Go (cron) + Alpaca API | Concurrent workers with token-bucket rate limiting |
| Cache | Redis 7 | Rate limiting deduplication, job completion tracking |
| ML Models | PyTorch + scikit-learn | Price prediction, regime detection |
| Charts | Apache ECharts | Candlestick, volume, prediction overlays |
| Testing | pytest + Playwright + k6 + Pact | Unit, E2E, load, contract tests |

---

## Project Structure

```
.
├── backend/                 # FastAPI application
│   ├── app/                 # Main application code
│   │   ├── api/             # API routes
│   │   ├── core/            # Config, auth, security
│   │   ├── ml/              # ML models & feature engineering
│   │   ├── models/          # SQLAlchemy models
│   │   └── services/        # Business logic
│   ├── rust/                # Rust native extension (market_features)
│   │   └── market_features/
│   │       ├── src/         # Rust source: rsi, macd, bollinger, features
│   │       └── tests/       # Rust unit tests
│   ├── tests/
│   │   ├── unit/            # Python unit tests
│   │   └── integration/     # Integration tests (DB, API, ML pipeline)
│   ├── Dockerfile           # Multi-stage: rust-builder -> py-builder -> runtime -> test
│   ├── entrypoint.sh        # Migration + uvicorn startup
│   └── requirements.txt     # Python dependencies (with Rust/polars comments)
│
├── scraper/                 # Go data scraper service
│   ├── cmd/scraper/         # main.go — cron scheduler
│   ├── internal/
│   │   ├── alpaca/          # Alpaca API client (crypto)
│   │   ├── vnstock/         # VNStock sidecar client
│   │   ├── db/              # PostgreSQL (pgx) persistence
│   │   ├── cache/           # Redis deduplication
│   │   ├── ratelimit/       # Token-bucket rate limiter
│   │   ├── config/          # Environment configuration
│   │   └── jobs/            # CryptoJob, VNStockJob
│   ├── Dockerfile           # Multi-stage Go build (distroless)
│   └── go.mod               # Go module definition
│
├── frontend/                # React SPA
│   ├── src/                 # TypeScript source
│   ├── __tests__/           # Vitest unit tests
│   ├── Dockerfile           # Multi-stage: deps -> test -> builder -> runtime
│   └── nginx.conf           # SPA routing fallback
│
├── e2e/                     # Playwright end-to-end tests
│   ├── tests/               # login, register, dashboard, role tests
│   ├── fixtures/            # AuthPage fixture + role-based users
│   └── helpers/             # Data cleanup helpers
│
├── contracts/               # Pact contract tests
│   ├── pact-consumer/tests/ # Frontend consumer contracts
│   └── pact-provider/tests/ # Backend provider verification
│
├── load-tests/              # k6 performance tests
│   └── api_smoke.js         # Smoke, soak, spike, chaos scenarios
│
├── tests/chaos/             # Chaos engineering
│   └── test_chaos.sh        # Latency, packet loss, blackout tests (toxiproxy)
│
├── .github/workflows/
│   └── ci.yml               # Full CI pipeline (see CI section)
│
├── docker-compose.yml       # All services + test dependencies
├── nginx/                   # Reverse proxy configuration
└── README.md                # This file
```

---

## Feature Engineering (Rust)

The `market_features` Rust crate accelerates technical indicator calculations:

| Indicator | Function | Speedup |
|-----------|----------|---------|
| RSI | `compute_rsi(prices, period=14)` | ~20x |
| MACD | `compute_macd(prices, fast, slow, signal)` | ~35x |
| Bollinger Bands | `compute_bollinger(prices, period, num_std)` | ~40x |
| Feature Engineering | `engineer_features_rs(close, high, low, volume)` | ~15x |

### Build the Rust Extension

```bash
cd backend/rust/market_features

# Install maturin
pip install maturin

# Build and install in current Python environment
maturin develop --release

# Build wheel for Docker
maturin build --release --out wheels/
```

### Rust Tests
```bash
cd backend/rust/market_features
cargo test
```

### Python Fallback
If the Rust extension is not available (e.g., ARM architecture, missing toolchain), `features.py` automatically falls back to the original Pandas implementation. No code changes needed.

---

## Data Scraper (Go)

The Go scraper handles concurrent data fetching with built-in rate limiting.

### Architecture
- **Token Bucket Rate Limiter**: Thread-safe atomic operations, supports per-source RPM limits
- **Alpaca Client**: Fetches crypto daily bars (BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD)
- **VNStock Client**: Proxies through the vnstock-sidecar for Vietnamese stocks (VCB, FPT, VNM, HPG, MSN)
- **Redis Deduplication**: Prevents re-scraping the same symbol on the same day
- **PostgreSQL UPSERT**: `ON CONFLICT (symbol, ts) DO UPDATE` for idempotent inserts

### Schedule
| Job | Cron (UTC) | Description |
|-----|-----------|-------------|
| Crypto | `0 0,2,4,6,8 * * *` | Every 2 hours starting midnight |
| VN Stocks | `0 14 * * *` | Daily at 14:00 UTC (≈ 21:00 VN time) |

### Configuration
Environment variables (defined in `.env`):
- `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` — Alpaca credentials
- `ALPACA_RATE_LIMIT_RPM` — Requests per minute (default: 200)
- `VNSTOCK_SLEEP_BETWEEN_TICKERS` — Seconds between VN stock requests (default: 2)
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string

### Build and Run Scraper Locally
```bash
cd scraper
go mod tidy
go build -o scraper ./cmd/scraper
./scraper
```

---

## CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs the full test matrix on every push/PR:

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit <service>
```

---

### Jobs

| Job | Trigger | Description |
|-----|---------|-------------|
| `backend-unit` | Push/PR | pytest with live PostgreSQL + Redis services |
| `frontend-unit` | Push/PR | vitest + production build |
| `scraper-unit` | Push/PR | Go tests with coverage |
| `contract-consumer` | Push/PR | Pact consumer tests, uploads pact artifacts |
| `contract-provider` | Push/PR | Downloads pacts, verifies against running backend |
| `integration` | Push/PR | DB insert/upsert, API endpoints, ML pipeline |
| `e2e` | Push/PR | Playwright tests: login, register, dashboard, role-based navigation |
| `load-test` | Push/PR | k6 smoke test against Docker stack |
| `chaos` | Push/PR | toxiproxy latency/packet-loss + blackout recovery |
| `build-push` | After all above pass | Build and push Docker images to GHCR |
| `security-scan` | After build-push | Trivy vulnerability scan on images |

### Nightly Schedule
At 02:00 UTC daily, the full pipeline (contract + integration + e2e) runs automatically.

### Test Results
- Coverage reports uploaded to Codecov
- Playwright reports uploaded as artifacts
- k6 metrics visible in GitHub Actions logs
- Pact contracts published to the Pact Broker (when configured)

---

## Testing

### Unit Tests
```bash
# Backend
cd backend && pytest tests/unit -v --cov=app

# Frontend
cd frontend && npx vitest run

# Scraper (unit + integration tests)
cd scraper && go test ./internal/... -v
```

### Integration Tests
```bash
# Backend integration tests (requires a running test database)
cd backend && pytest tests/integration -v

# Scraper integration tests (uses testcontainers, no external services needed)
cd scraper && go test ./internal/db/ -v
cd scraper && go test ./internal/cache/ -v
```

### Contract Tests
```bash
# Consumer
cd backend && pytest contracts/pact-consumer/tests -v

# Provider (run after consumer)
cd backend && pytest contracts/pact-provider/tests -v
```

### E2E Tests
```bash
# 1. Start the full stack
docker compose up -d --build

# 2. Install Playwright
cd e2e && npm install && npx playwright install chromium

# 3. Run tests
npx playwright test

# 4. View report
npx playwright show-report
```

### Load Tests
```bash
# Start stack first
docker compose up -d

# Run k6
docker run --rm --network host \
  -v $(pwd)/load-tests:/tests \
  grafana/k6:latest run /tests/api_smoke.js
```

### Chaos Tests
```bash
# Requires toxiproxy running alongside the stack
docker run -d --name toxiproxy --network host ghcr.io/shopify/toxiproxy

# Run chaos suite
./tests/chaos/test_chaos.sh
```

---

## Docker Reference

### Multi-Stage Builds

| Service | Stages | Notes |
|---------|--------|-------|
| Backend | rust-builder → py-builder → runtime → test | Rust extension compiled in stage 1 |
| Frontend | deps → test → builder → runtime | Tests run before build |
| Scraper | builder → distroless | Static Go binary, minimal attack surface |
| VNStock Sidecar | python-slim | Isolated vnstock3 process |

### Test Dependency Chain
```
postgres + redis ──► backend-test
               └──► scraper-test
               └──► frontend-test
```

All test containers exit after completing their suite; the application stack remains independent.

---

## Development

### Backend (Python)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install maturin
cd rust/market_features && maturin develop --release
uvicorn app.main:app --reload
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev      # Vite dev server
npm run test     # Vitest watch mode
```

### Scraper (Go)
```bash
cd scraper
go mod tidy
go run ./cmd/scraper
```

---

## License

MIT License — see LICENSE file for details.
