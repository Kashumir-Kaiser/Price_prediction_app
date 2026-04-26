package jobs

import (
	"context"
	"fmt"
	"time"

	"scraper/internal/alpaca"
	"scraper/internal/cache"
	"scraper/internal/db"
	"scraper/internal/ratelimit"

	"go.uber.org/zap"
)

// CryptoJob fetches Alpaca crypto data for a list of symbols.
func CryptoJob(
	ctx context.Context,
	logger *zap.Logger,
	alpacaClient *alpaca.Client,
	postgres *db.Postgres,
	redis *cache.Redis,
	rateLimiter *ratelimit.TokenBucket,
	symbols []string,
) error {
	for _, symbol := range symbols {
		if err := ctx.Err(); err != nil {
			return err
		}

		// Check if already scraped today
		today := time.Now().Format("2006-01-02")
		done, err := redis.IsComplete(ctx, today, symbol, "crypto")
		if err != nil {
			logger.Warn("redis check failed", zap.Error(err))
		}
		if done {
			logger.Info("skipping already-scraped symbol", zap.String("symbol", symbol))
			continue
		}

		// Rate limit before request
		if err := rateLimiter.Wait(ctx); err != nil {
			return fmt.Errorf("rate limiter: %w", err)
		}

		bars, err := alpacaClient.FetchLatestBar(ctx, symbol)
		if err != nil {
			logger.Error("alpaca fetch failed", zap.String("symbol", symbol), zap.Error(err))
			continue
		}

		for _, bar := range bars {
			if err := postgres.SaveCryptoBar(ctx, symbol, bar.Timestamp, bar.Open, bar.High, bar.Low, bar.Close, bar.Volume); err != nil {
				logger.Error("db save failed", zap.String("symbol", symbol), zap.Error(err))
				continue
			}
			logger.Info("saved crypto bar", zap.String("symbol", symbol), zap.Time("ts", bar.Timestamp))
		}
		if err := redis.MarkComplete(ctx, today, symbol, "crypto", 48*time.Hour); err != nil {
			logger.Warn("redis mark complete failed", zap.Error(err))
		}
	}
	return nil
}
