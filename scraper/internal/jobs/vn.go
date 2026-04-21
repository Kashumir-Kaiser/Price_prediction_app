package jobs

import (
	"context"
	"time"

	"github.com/yourorg/market-scraper/internal/cache"
	"github.com/yourorg/market-scraper/internal/db"
	"github.com/yourorg/market-scraper/internal/vnstock"
	"go.uber.org/zap"
)

// VNStockJob fetches daily VN stock OHLCV bars via the vnstock sidecar.
func VNStockJob(
	ctx context.Context,
	logger *zap.Logger,
	vnClient *vnstock.Client,
	postgres *db.Postgres,
	redis *cache.Redis,
	symbols []string,
	sleepSeconds int,
) error {
	for _, symbol := range symbols {
		if err := ctx.Err(); err != nil {
			return err
		}

		// Check if already scraped today
		today := time.Now().Format("2006-01-02")
		done, err := redis.IsComplete(ctx, today, symbol, "vnstock")
		if err != nil {
			logger.Warn("redis check failed", zap.Error(err))
		}
		if done {
			logger.Info("skipping already-scraped symbol", zap.String("symbol", symbol))
			continue
		}

		bars, err := vnClient.FetchOHLCV(ctx, symbol)
		if err != nil {
			logger.Error("vnstock fetch failed", zap.String("symbol", symbol), zap.Error(err))
			continue
		}

		for _, bar := range bars {
			ts, _ := time.Parse("2006-01-02", bar.Ts)
			if err := postgres.SaveStockBar(ctx, symbol, ts, bar.Open, bar.High, bar.Low, bar.Close, bar.Volume, "vnstock"); err != nil {
				logger.Error("db save failed", zap.String("symbol", symbol), zap.Error(err))
				continue
			}
			logger.Info("saved vn bar", zap.String("symbol", symbol), zap.String("ts", bar.Ts))
		}

		if err := redis.MarkComplete(ctx, today, symbol, "vnstock", 48*time.Hour); err != nil {
			logger.Warn("redis mark complete failed", zap.Error(err))
		}

		// Sleep between requests to avoid hammering the sidecar
		time.Sleep(time.Duration(sleepSeconds) * time.Second)
	}
	return nil
}
