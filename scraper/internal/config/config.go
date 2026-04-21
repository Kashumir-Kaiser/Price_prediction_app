package config

import (
	"os"
	"strconv"
)

// Config holds environment-driven configuration (mirrors Python .env).
type Config struct {
	DatabaseURL          string
	RedisURL             string
	AlpacaKey            string
	AlpacaSecret         string
	AlpacaRateLimitRPM   int
	VNStockSleepSeconds  int
}

func Load() *Config {
	rpm, _ := strconv.Atoi(getenv("ALPACA_RATE_LIMIT_RPM", "200"))
	sleep, _ := strconv.Atoi(getenv("VNSTOCK_SLEEP_BETWEEN_TICKERS", "2"))
	return &Config{
		DatabaseURL:         getenv("DATABASE_URL", "postgresql://market_user:change_me@postgres:5432/market_db"),
		RedisURL:            getenv("REDIS_URL", "redis://redis:6379/0"),
		AlpacaKey:           getenv("ALPACA_API_KEY", ""),
		AlpacaSecret:        getenv("ALPACA_SECRET_KEY", ""),
		AlpacaRateLimitRPM:  rpm,
		VNStockSleepSeconds: sleep,
	}
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
