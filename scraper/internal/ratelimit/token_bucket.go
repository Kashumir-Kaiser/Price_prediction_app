package ratelimit

import (
	"context"
	"sync/atomic"
	"time"
)

// TokenBucket is a thread-safe token-bucket rate limiter.
type TokenBucket struct {
	tokens   atomic.Int64
	capacity int64
}

// NewTokenBucket creates a bucket and starts the refill goroutine.
func NewTokenBucket(capacity int64, ratePerSecond float64) *TokenBucket {
	tb := &TokenBucket{capacity: capacity}
	tb.tokens.Store(capacity) // start full
	tickDuration := time.Duration(float64(time.Second) / ratePerSecond)
	go func() {
		ticker := time.NewTicker(tickDuration)
		defer ticker.Stop()
		for range ticker.C {
			for {
				cur := tb.tokens.Load()
				if cur >= capacity {
					break
				}
				if tb.tokens.CompareAndSwap(cur, cur+1) {
					break
				}
			}
		}
	}()
	return tb
}

// Wait blocks until a token is available or ctx is cancelled.
func (tb *TokenBucket) Wait(ctx context.Context) error {
	for {
		cur := tb.tokens.Load()
		if cur > 0 && tb.tokens.CompareAndSwap(cur, cur-1) {
			return nil
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(50 * time.Millisecond):
			// retry
		}
	}
}
