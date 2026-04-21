package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/robfig/cron/v3"
	"github.com/yourorg/market-scraper/internal/alpaca"
	"github.com/yourorg/market-scraper/internal/cache"
	"github.com/yourorg/market-scraper/internal/config"
	"github.com/yourorg/market-scraper/internal/db"
	"github.com/yourorg/market-scraper/internal/jobs"
	"github.com/yourorg/market-scraper/internal/ratelimit"
	"github.com/yourorg/market-scraper/internal/vnstock"
	"go.uber.org/zap"
)

func main() {
	// Logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	// Config
	cfg := config.Load()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Database
	postgres, err := db.NewPostgres(ctx, cfg.DatabaseURL)
	if err != nil {
		logger.Fatal("failed to connect to postgres", zap.Error(err))
	}
	defer postgres.Pool.Close()

	// Cache
	redis, err := cache.NewRedis(cfg.RedisURL)
	if err != nil {
		logger.Fatal("failed to connect to redis", zap.Error(err))
	}

	// Alpaca rate limiter: 200 RPM = 3.333 requests/second
	// Use capacity 5 (slightly above 3.33) for burst safety
	alpacaLimiter := ratelimit.NewTokenBucket(5, float64(cfg.AlpacaRateLimitRPM)/60.0)

	// Clients
	alpacaClient := alpaca.NewClient(cfg.AlpacaKey, cfg.AlpacaSecret)

	// Symbol lists
	cryptoSymbols := []string{"BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "DOGE/USD"}
	vnSymbols := []string{"VCB", "FPT", "VNM", "HPG", "MSN"}

	// Cron scheduler
	c := cron.New(cron.WithSeconds())

	// Crypto cron: 00:00, 02:00, 04:00, 06:00, 08:00 UTC
	c.AddFunc("0 0 0,2,4,6,8 * * *", func() {
		logger.Info("starting crypto scrape")
		if err := jobs.CryptoJob(ctx, logger, alpacaClient, postgres, redis, alpacaLimiter, cryptoSymbols); err != nil {
			logger.Error("crypto job failed", zap.Error(err))
		}
	})

	// VN stocks cron: 14:00 UTC (≈ 21:00 VN time)
	c.AddFunc("0 0 14 * * *", func() {
		logger.Info("starting vnstock scrape")
		if err := jobs.VNStockJob(ctx, logger, vnstock.NewClient(), postgres, redis, vnSymbols, cfg.VNStockSleepSeconds); err != nil {
			logger.Error("vnstock job failed", zap.Error(err))
		}
	})

	c.Start()
	logger.Info("scraper scheduler started")

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	logger.Info("shutting down gracefully")
	cancel()
	<-c.Stop().Done()
	fmt.Println("scraper stopped")
}
