package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// Cache interface for the scraper.
type Cache interface {
	Get(ctx context.Context, key string, dest interface{}) error
	Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
	HealthCheck(ctx context.Context) error
}

// RedisCache implements Cache with Redis backend.
type RedisCache struct {
	client *redis.Client
}

// Redis wraps the go-redis client and provides job-completion tracking.
type Redis struct {
	client *redis.Client
}

// NewRedisCache creates a new Redis cache.
func NewRedisCache(client *redis.Client) *RedisCache {
	return &RedisCache{client: client}
}

// NewRedis creates a new Redis completion tracker from a URL.
func NewRedis(url string) (*Redis, error) {
	opts, err := redis.ParseURL(url)
	if err != nil {
		return nil, fmt.Errorf("parse redis url: %w", err)
	}
	client := redis.NewClient(opts)
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, err
	}
	return &Redis{client: client}, nil
}

// IsComplete checks whether key "scrape:{date}:{symbol}:{source}" exists.
func (r *Redis) IsComplete(ctx context.Context, date, symbol, source string) (bool, error) {
	key := fmt.Sprintf("scrape:%s:%s:%s", date, symbol, source)
	n, err := r.client.Exists(ctx, key).Result()
	if err != nil {
		return false, err
	}
	return n > 0, nil
}

// MarkComplete sets a key to mark a job as done, with a TTL.
func (r *Redis) MarkComplete(ctx context.Context, date, symbol, source string, ttl time.Duration) error {
	key := fmt.Sprintf("scrape:%s:%s:%s", date, symbol, source)
	return r.client.Set(ctx, key, "1", ttl).Err()
}

// Get retrieves and unmarshals a value from Redis.
func (c *RedisCache) Get(ctx context.Context, key string, dest interface{}) error {
	data, err := c.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return fmt.Errorf("key %q not found", key)
	}
	if err != nil {
		return fmt.Errorf("redis GET: %w", err)
	}

	if err := json.Unmarshal([]byte(data), dest); err != nil {
		return fmt.Errorf("unmarshal: %w", err)
	}

	return nil
}

// Set marshals and stores a value in Redis with TTL.
func (c *RedisCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}

	if err := c.client.Set(ctx, key, data, ttl).Err(); err != nil {
		return fmt.Errorf("redis SET: %w", err)
	}

	return nil
}

// Delete removes a key from Redis.
func (c *RedisCache) Delete(ctx context.Context, key string) error {
	if err := c.client.Del(ctx, key).Err(); err != nil {
		return fmt.Errorf("redis DEL: %w", err)
	}
	return nil
}

// HealthCheck pings Redis to verify connectivity.
func (c *RedisCache) HealthCheck(ctx context.Context) error {
	return c.client.Ping(ctx).Err()
}
