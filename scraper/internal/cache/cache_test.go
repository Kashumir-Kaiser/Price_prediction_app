package cache_test

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/wait"

	"scraper/internal/cache"
)

func TestRedisCompletionTracking(t *testing.T) {
	ctx := context.Background()
	req := testcontainers.ContainerRequest{
		Image:        "redis:7-alpine",
		ExposedPorts: []string{"6379/tcp"},
		WaitingFor:   wait.ForLog("Ready to accept connections"),
	}
	container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
		ContainerRequest: req,
		Started:          true,
	})
	require.NoError(t, err)
	defer container.Terminate(ctx)

	host, _ := container.Host(ctx)
	port, _ := container.MappedPort(ctx, "6379")
	redisURL := "redis://" + host + ":" + port.Port()

	r, err := cache.NewRedis(redisURL)
	require.NoError(t, err)

	date := "2026-04-26"
	symbol := "BTC/USD"
	source := "crypto"

	complete, err := r.IsComplete(ctx, date, symbol, source)
	assert.NoError(t, err)
	assert.False(t, complete)

	err = r.MarkComplete(ctx, date, symbol, source, 1*time.Minute)
	assert.NoError(t, err)

	complete, err = r.IsComplete(ctx, date, symbol, source)
	assert.NoError(t, err)
	assert.True(t, complete)
}
