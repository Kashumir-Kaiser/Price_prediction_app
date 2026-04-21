package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Postgres wraps a connection pool.
type Postgres struct {
	Pool *pgxpool.Pool
}

// NewPostgres creates a connection pool from a DSN.
func NewPostgres(ctx context.Context, dsn string) (*Postgres, error) {
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, err
	}
	config.MaxConns = 10
	config.MaxConnLifetime = 30 * time.Minute
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		return nil, err
	}
	if err := pool.Ping(ctx); err != nil {
		return nil, err
	}
	return &Postgres{Pool: pool}, nil
}

// SaveCryptoBar inserts a single crypto bar into ohlcv_crypto (UPSERT on symbol+ts).
func (p *Postgres) SaveCryptoBar(ctx context.Context, symbol string, ts time.Time, o, h, l, c, v, vw float64, src string) error {
	q := `
INSERT INTO ohlcv_crypto (symbol, ts, open, high, low, close, volume, vwap)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (symbol, ts) DO UPDATE SET
  open   = EXCLUDED.open,
  high   = EXCLUDED.high,
  low    = EXCLUDED.low,
  close  = EXCLUDED.close,
  volume = EXCLUDED.volume,
  vwap   = EXCLUDED.vwap;
`
	_, err := p.Pool.Exec(ctx, q, symbol, ts, o, h, l, c, v, vw)
	return err
}

// SaveStockBar inserts a single stock bar into ohlcv_stocks (UPSERT on symbol+ts).
func (p *Postgres) SaveStockBar(ctx context.Context, symbol string, ts time.Time, o, h, l, c, v float64, src string) error {
	q := `
INSERT INTO ohlcv_stocks (symbol, ts, open, high, low, close, volume)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (symbol, ts) DO UPDATE SET
  open   = EXCLUDED.open,
  high   = EXCLUDED.high,
  low    = EXCLUDED.low,
  close  = EXCLUDED.close,
  volume = EXCLUDED.volume;
`
	_, err := p.Pool.Exec(ctx, q, symbol, ts, o, h, l, c, v)
	return err
}

// SaveCryptoBars inserts a batch of crypto bars in a single transaction.
func (p *Postgres) SaveCryptoBars(ctx context.Context, symbol string, bars []CryptoBar) error {
	batch := &pgx.Batch{}
	for _, b := range bars {
		batch.Queue(`
INSERT INTO ohlcv_crypto (symbol, ts, open, high, low, close, volume, vwap)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (symbol, ts) DO UPDATE SET
  open   = EXCLUDED.open,
  high   = EXCLUDED.high,
  low    = EXCLUDED.low,
  close  = EXCLUDED.close,
  volume = EXCLUDED.volume,
  vwap   = EXCLUDED.vwap;
`, symbol, b.Timestamp, b.Open, b.High, b.Low, b.Close, b.Volume, b.VWAP)
	}
	results := p.Pool.SendBatch(ctx, batch)
	defer results.Close()
	_, err := results.Exec()
	return err
}

// SaveStockBars inserts a batch of stock bars in a single transaction.
func (p *Postgres) SaveStockBars(ctx context.Context, symbol string, bars []StockBar) error {
	batch := &pgx.Batch{}
	for _, b := range bars {
		batch.Queue(`
INSERT INTO ohlcv_stocks (symbol, ts, open, high, low, close, volume)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (symbol, ts) DO UPDATE SET
  open   = EXCLUDED.open,
  high   = EXCLUDED.high,
  low    = EXCLUDED.low,
  close  = EXCLUDED.close,
  volume = EXCLUDED.volume;
`, symbol, b.Timestamp, b.Open, b.High, b.Low, b.Close, b.Volume)
	}
	results := p.Pool.SendBatch(ctx, batch)
	defer results.Close()
	_, err := results.Exec()
	return err
}

type CryptoBar struct {
	Timestamp time.Time
	Open      float64
	High      float64
	Low       float64
	Close     float64
	Volume    float64
	VWAP      float64
}

type StockBar struct {
	Timestamp time.Time
	Open      float64
	High      float64
	Low       float64
	Close     float64
	Volume    float64
}
