package session

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/collider/moos/internal/morphism"
	"github.com/redis/go-redis/v9"
)

const (
	// cacheKeyPrefix is the Redis key prefix for active-state projections.
	// Keys are of the form "moos:active:{scopeURN}".
	cacheKeyPrefix = "moos:active:"
	// cacheChannelPrefix is the Redis pub/sub channel prefix for morphism deltas.
	// Channels are of the form "moos:delta:{scopeURN}".
	cacheChannelPrefix = "moos:delta:"
)

// ActiveStateCache maintains a Redis-backed projection of the latest morphism
// envelope applied to each scope URN. It serves two purposes:
//
//  1. point-in-time read — any surface can call Get to learn the current state
//     of a scope without replaying the full morphism log from PostgreSQL.
//
//  2. fan-out — after applying a morphism the session manager calls Publish,
//     which writes to a Redis pub/sub channel so that any number of listeners
//     (e.g. WebSocket surfaces, edge cache workers) receive the delta in
//     near-real time.
//
// When no Redis URL is configured, callers receive a no-op nopActiveStateCache.
// Use NewActiveStateCache to construct an instance; its zero value is invalid.
type ActiveStateCache struct {
	client *redis.Client
	ttl    time.Duration
}

// NewActiveStateCache creates a live Redis-backed cache. Returns an error if
// the Redis URL is empty or if an initial PING fails.
func NewActiveStateCache(redisURL string, ttl time.Duration) (*ActiveStateCache, error) {
	if redisURL == "" {
		return nil, fmt.Errorf("active state cache: redis URL is required")
	}
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("active state cache: invalid redis URL: %w", err)
	}
	client := redis.NewClient(opts)
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := client.Ping(ctx).Err(); err != nil {
		_ = client.Close()
		return nil, fmt.Errorf("active state cache: redis ping failed: %w", err)
	}
	if ttl <= 0 {
		ttl = 24 * time.Hour
	}
	return &ActiveStateCache{client: client, ttl: ttl}, nil
}

// Close releases the underlying Redis connection.
func (c *ActiveStateCache) Close() error { return c.client.Close() }

func scopeKey(scopeURN string) string {
	return cacheKeyPrefix + sanitizeURN(scopeURN)
}

func scopeChannel(scopeURN string) string {
	return cacheChannelPrefix + sanitizeURN(scopeURN)
}

// sanitizeURN replaces characters that would cause Redis key issues.
func sanitizeURN(urn string) string {
	return strings.ReplaceAll(urn, " ", "_")
}

// Set stores the latest morphism envelope for the given scope URN. The entry
// expires after the configured TTL so stale scopes do not accumulate.
func (c *ActiveStateCache) Set(ctx context.Context, scopeURN string, envelope morphism.Envelope) error {
	data, err := json.Marshal(envelope)
	if err != nil {
		return fmt.Errorf("active state cache set: marshal: %w", err)
	}
	return c.client.Set(ctx, scopeKey(scopeURN), data, c.ttl).Err()
}

// Get retrieves the latest morphism envelope for a scope URN.
// Returns (envelope, true, nil) on hit; (zero, false, nil) on miss.
func (c *ActiveStateCache) Get(ctx context.Context, scopeURN string) (morphism.Envelope, bool, error) {
	data, err := c.client.Get(ctx, scopeKey(scopeURN)).Bytes()
	if err == redis.Nil {
		return morphism.Envelope{}, false, nil
	}
	if err != nil {
		return morphism.Envelope{}, false, fmt.Errorf("active state cache get: %w", err)
	}
	var envelope morphism.Envelope
	if err := json.Unmarshal(data, &envelope); err != nil {
		return morphism.Envelope{}, false, fmt.Errorf("active state cache get: unmarshal: %w", err)
	}
	return envelope, true, nil
}

// Publish writes the morphism envelope to the Redis pub/sub channel for the
// given scope URN, enabling fan-out to any number of subscribers.
func (c *ActiveStateCache) Publish(ctx context.Context, scopeURN string, envelope morphism.Envelope) error {
	data, err := json.Marshal(envelope)
	if err != nil {
		return fmt.Errorf("active state cache publish: marshal: %w", err)
	}
	return c.client.Publish(ctx, scopeChannel(scopeURN), data).Err()
}

// Subscribe returns a channel that receives morphism deltas for a scope URN, and
// a cancel function that unsubscribes and closes the channel. The subscription
// lives until ctx is cancelled or cancel is called.
func (c *ActiveStateCache) Subscribe(ctx context.Context, scopeURN string) (<-chan morphism.Envelope, func(), error) {
	sub := c.client.Subscribe(ctx, scopeChannel(scopeURN))
	ch := make(chan morphism.Envelope, 32)
	cancel := func() {
		_ = sub.Close()
		close(ch)
	}
	go func() {
		redisCh := sub.Channel()
		for {
			select {
			case <-ctx.Done():
				return
			case msg, ok := <-redisCh:
				if !ok {
					return
				}
				var envelope morphism.Envelope
				if err := json.Unmarshal([]byte(msg.Payload), &envelope); err != nil {
					continue
				}
				select {
				case ch <- envelope:
				case <-ctx.Done():
					return
				}
			}
		}
	}()
	return ch, cancel, nil
}

// activeStateProjector is the interface consumed by the session manager.
// It is satisfied by *ActiveStateCache and by nopActiveStateCache.
type activeStateProjector interface {
	Set(ctx context.Context, scopeURN string, envelope morphism.Envelope) error
	Publish(ctx context.Context, scopeURN string, envelope morphism.Envelope) error
}

// nopActiveStateCache is the no-op implementation used when Redis is absent.
type nopActiveStateCache struct{}

func (nopActiveStateCache) Set(_ context.Context, _ string, _ morphism.Envelope) error {
	return nil
}
func (nopActiveStateCache) Publish(_ context.Context, _ string, _ morphism.Envelope) error {
	return nil
}
