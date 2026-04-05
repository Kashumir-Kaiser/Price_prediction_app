# Stock & Crypto Price Prediction Platform

A production-quality MVP of a stock & crypto price-prediction platform. The system ingests market data from Alpaca Markets and vnstock, trains lightweight ML models (Random Forest, XGBoost, LSTM), exposes a REST API, and presents predictions in a clean React dashboard.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│    Nginx    │────▶│   FastAPI   │
│  Frontend   │     │   Reverse   │     │   Backend   │
│             │◀────│    Proxy    │◀────│             │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                       ┌────────────────────────┼────────────────────────┐
                       │                        │                        │
                       ▼                        ▼                        ▼
                ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
                │  PostgreSQL │         │    Redis    │         │  Model Cache│
                │   (Data)    │         │   (Cache)   │         │  (Volume)   │
                └─────────────┘         └─────────────┘         └─────────────┘
                       ▲
                       │
                ┌──────┴──────┐
                │   Scraper   │
                │ (Scheduler) │
                └─────────────┘
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
- Docker & Docker Compose
- Alpaca Markets API key (free tier)

### 1. Clone and Configure

```bash
cd stock-prediction-app

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# ALPACA_API_KEY=your_key_here
# ALPACA_SECRET_KEY=your_secret_here
```

### 2. Run with Docker Compose

```bash
# Build and start all services
docker compose up --build

# Or run in detached mode
docker compose up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost
- **API Docs**: http://localhost/api/docs (Swagger UI)
- **API Health**: http://localhost/api/health

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v --cov

# Run locally (requires PostgreSQL and Redis)
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Scraper Development

```bash
cd scraper

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run scheduler locally
python scheduler.py
```

## Scaling

### Baseline (10 concurrent users)
The default `docker-compose.yml` is configured for up to 10 concurrent users:
- 1× backend container (2 Uvicorn workers, 1GB memory limit)
- 1× scraper container
- 1× PostgreSQL (512MB memory limit)
- 1× Redis (160MB memory limit)

### Scale-up (50 concurrent users)
Apply production overrides:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Changes:
- 3× backend replicas (4 workers each, 1.5GB memory limit)
- PostgreSQL: max_connections=200, 1GB memory limit
- Redis: 256MB memory limit

## Project Structure

```
stock-prediction-app/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # External API integrations
│   │   ├── ml/            # ML pipeline
│   │   ├── db/            # Database models & CRUD
│   │   └── utils/         # Utilities (rate limiter, logger)
│   ├── tests/             # Backend unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── scraper/                # Data ingestion service
│   ├── jobs/              # APScheduler jobs
│   ├── tests/             # Scraper unit tests
│   ├── Dockerfile
│   └── scheduler.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── store/         # Zustand store
│   │   ├── api/           # API client
│   │   └── types/         # TypeScript types
│   ├── tests/             # Frontend unit tests
│   └── Dockerfile
├── nginx/                  # Nginx configuration
│   └── nginx.conf
├── model-cache/           # Docker volume for ML models
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

## OOM-Safe Model Loading

Models are never downloaded during Docker image build. They are:
1. Stored in a named Docker volume (`model-cache`)
2. Lazy-loaded on first prediction request
3. Cached in process-level memory
4. Loaded with `map_location='cpu'` for CPU-only inference

## API Rate Limits

### Alpaca Markets (Free Tier)
- 200 requests/minute per API key
- 1-year historical range
- 1,000 bars per request (paginated)

### vnstock (Guest Mode)
- ~30 requests/minute
- 5-year historical range (TCBS)
- 2-second sleep between ticker fetches

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALPACA_API_KEY` | Alpaca API key | Required |
| `ALPACA_SECRET_KEY` | Alpaca secret key | Required |
| `POSTGRES_*` | PostgreSQL connection | See .env.example |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `API_KEY` | Internal API key for frontend | `internal_x_api_key` |
| `MODEL_CACHE_DIR` | Model cache directory | `/model-cache` |
| `MODEL_BASE_URL` | (Optional) Pre-trained model URL | None |

## Testing

### Run All Tests

```bash
# Backend tests
cd backend && pytest tests/ -v --cov

# Scraper tests
cd scraper && pytest tests/ -v

# Frontend tests
cd frontend && npm test
```

### Test Coverage Requirements
- Backend: ≥80% coverage on service modules
- Frontend: All key components tested
- Scraper: All job functions tested

## Troubleshooting

### Container fails to start
```bash
# Check logs
docker compose logs -f [service_name]

# Rebuild specific service
docker compose up -d --build [service_name]
```

### Database connection issues
```bash
# Reset database volume (WARNING: data loss)
docker compose down -v
docker compose up -d
```

### Model not found errors
Models need to be trained before predictions work. The scraper will populate historical data, but ML models need to be trained via the API or training scripts.

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open a GitHub issue.
