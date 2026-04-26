Realized probably wise to keep every patches in a note.md so it's easier to see what changes

| Area | What was done |
|-------|-----------|
|Auth | Unified on useGlobalStore (localStorage), removed useAuthStore. Login/register pages correctly call globalLogin. Dashboard reads user from global store.|
|Data flow | Scraper tables aligned with backend ORM (crypto_bars / stock_bars), price endpoint returns real DB data.|
|Rust | Import path corrected to market_features.|
|Docker | Test services extracted to docker-compose.test.yml, main compose now starts without hanging.|
|E2E | data-testid attributes added to login/register controls and asset buttons; E2E tests updated accordingly.|
|Rate limiting | Auth rate limiter is now per‑IP.|
|Prediction | Direction mapping fixed (binary up/down).|
|Retrain | BackgroundTasks parameter order corrected; placeholder function added.|
|Scraper jobs | Calls to SaveCryptoBar/SaveStockBar updated to match simplified signatures (no vwap or source).|
|Testing | Added useGlobalStore.test.ts, Go integration tests for db + cache, removed old useAuthStore.test.ts.|
|Timezone | RequestLog now uses timezone‑aware timestamps.|
|Config | cors_origins field added to settings.|