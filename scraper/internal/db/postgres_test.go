package db_test

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"

	"scraper/internal/db"
)

func TestSaveCryptoBar_Upsert(t *testing.T) {
	ctx := context.Background()

	// 1. Start a Postgres container
	req := testcontainers.ContainerRequest{
		Image:        "postgres:16-alpine",
		ExposedPorts: []string{"5432/tcp"},
		Env: map[string]string{
			"POSTGRES_DB":       "testdb",
			"POSTGRES_USER":     "testuser",
			"POSTGRES_PASSWORD": "testpass",
		},
		WaitingFor: wait.ForListeningPort("5432/tcp"),
	}
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	require.NoError(t, err)
	defer container.Terminate(ctx)

	host, err := container.Host(ctx)
	require.NoError(t, err)
	port, err := container.MappedPort(ctx, "5432")
	require.NoError(t, err)
	dsn := fmt.Sprintf("postgresql://testuser:testpass@%s:%d/testdb?sslmode=disable", host, port.Int())

	// 2. Create connection pool
	pool, err := pgxpool.New(ctx, dsn)
	require.NoError(t, err)
	defer pool.Close()

	// 3. Create the table that matches the actual schema (crypto_bars)
	_, err = pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS crypto_bars (
			id SERIAL PRIMARY KEY,
			symbol VARCHAR(32) NOT NULL,
			ts TIMESTAMPTZ NOT NULL,
			open NUMERIC(18,8) NOT NULL,
			high NUMERIC(18,8),
			low NUMERIC(18,8),
			close NUMERIC(18,8),
			volume NUMERIC(24,8),
			UNIQUE(symbol, ts)
		);
	`)
	require.NoError(t, err)

	// 4. Instantiate the repo that will be tested
	repo := &db.Postgres{Pool: pool}

	// 5. Insert a bar
	ts := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	err = repo.SaveCryptoBar(ctx, "BTC/USD", ts, 100.0, 110.0, 90.0, 105.0, 1000.0)
	require.NoError(t, err)

	// 6. Verify the insert
	var close float64
	err = pool.QueryRow(ctx, "SELECT close FROM crypto_bars WHERE symbol=$1 AND ts=$2", "BTC/USD", ts).Scan(&close)
	require.NoError(t, err)
	assert.Equal(t, 105.0, close)

	// 7. Upsert with a new close price
	err = repo.SaveCryptoBar(ctx, "BTC/USD", ts, 100.0, 110.0, 90.0, 200.0, 2000.0)
	require.NoError(t, err)

	// 8. Verify the update
	err = pool.QueryRow(ctx, "SELECT close FROM crypto_bars WHERE symbol=$1 AND ts=$2", "BTC/USD", ts).Scan(&close)
	require.NoError(t, err)
	assert.Equal(t, 200.0, close)
}
