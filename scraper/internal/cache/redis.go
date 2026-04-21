package cache

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// Redis wraps the go-redis client.
type Redis struct {
	Client *redis.Client
}

// NewRedis parses a redis:// URL and returns a Redis wrapper.
func NewRedis(redisURL string) (*Redis, error) {
	// Simple parsing for redis://host:port/db format
	var addr, password string
	var db int
	// Use a simplified parser — in production use url.Parse
	fmt.Sscanf(redisURL, "redis://%s/%d", &addr, &db)
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       db,
	})
	return &Redis{Client: client}, nil
}

// Set stores a key with TTL.
func (r *Redis) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	return r.Client.Set(ctx, key, value, ttl).Err()
}

// Get retrieves a string value.
func (r *Redis) Get(ctx context.Context, key string) (string, error) {
	return r.Client.Get(ctx, key).Result()
}

// IsComplete checks whether a scraping run has been completed (key exists).
func (r *Redis) IsComplete(ctx context.Context, date, symbol, job string) (bool, error) {
	key := fmt.Sprintf("done:%s:%s:%s", date, symbol, job)
	exists, err := r.Client.Exists(ctx, key).Result()
	return exists > 0, err
}

// MarkComplete records that a scraping run was completed successfully.
func (r *Redis) MarkComplete(ctx context.Context, date, symbol, job string, ttl time.Duration) error {
	key := fmt.Sprintf("done:%s:%s:%s", date, symbol, job)
	return r.Client.Set(ctx, key, "1", ttl).Err()
}
