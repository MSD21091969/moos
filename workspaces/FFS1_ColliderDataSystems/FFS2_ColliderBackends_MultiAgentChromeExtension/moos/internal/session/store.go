package session

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/collider/moos/internal/model"
	"github.com/redis/go-redis/v9"
)

type sessionSnapshot struct {
	Summary  Summary         `json:"summary"`
	Messages []model.Message `json:"messages"`
}

type store interface {
	Save(ctx context.Context, snapshot sessionSnapshot) error
	Delete(ctx context.Context, sessionID string) error
	List(ctx context.Context) ([]sessionSnapshot, error)
}

type memoryStore struct {
	mu    sync.RWMutex
	items map[string]sessionSnapshot
}

func newMemoryStore() *memoryStore {
	return &memoryStore{items: map[string]sessionSnapshot{}}
}

func (store *memoryStore) Save(ctx context.Context, snapshot sessionSnapshot) error {
	_ = ctx
	store.mu.Lock()
	defer store.mu.Unlock()
	store.items[snapshot.Summary.SessionID] = snapshot
	return nil
}

func (store *memoryStore) Delete(ctx context.Context, sessionID string) error {
	_ = ctx
	store.mu.Lock()
	defer store.mu.Unlock()
	delete(store.items, sessionID)
	return nil
}

func (store *memoryStore) List(ctx context.Context) ([]sessionSnapshot, error) {
	_ = ctx
	store.mu.RLock()
	defer store.mu.RUnlock()
	result := make([]sessionSnapshot, 0, len(store.items))
	for _, item := range store.items {
		result = append(result, item)
	}
	return result, nil
}

type redisStore struct {
	client *redis.Client
	prefix string
	ttl    time.Duration
}

func newRedisStore(redisURL string, ttl time.Duration) (*redisStore, error) {
	options, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, err
	}
	return &redisStore{client: redis.NewClient(options), prefix: "moos:session:", ttl: ttl}, nil
}

func (store *redisStore) key(sessionID string) string {
	return store.prefix + sessionID
}

func (store *redisStore) Save(ctx context.Context, snapshot sessionSnapshot) error {
	encoded, err := json.Marshal(snapshot)
	if err != nil {
		return err
	}
	return store.client.Set(ctx, store.key(snapshot.Summary.SessionID), encoded, store.ttl).Err()
}

func (store *redisStore) Delete(ctx context.Context, sessionID string) error {
	return store.client.Del(ctx, store.key(sessionID)).Err()
}

func (store *redisStore) List(ctx context.Context) ([]sessionSnapshot, error) {
	keys, err := store.client.Keys(ctx, store.prefix+"*").Result()
	if err != nil {
		return nil, err
	}
	result := make([]sessionSnapshot, 0, len(keys))
	for _, key := range keys {
		raw, getErr := store.client.Get(ctx, key).Result()
		if getErr != nil {
			continue
		}
		var snapshot sessionSnapshot
		if decodeErr := json.Unmarshal([]byte(raw), &snapshot); decodeErr != nil {
			continue
		}
		if snapshot.Summary.SessionID == "" {
			continue
		}
		result = append(result, snapshot)
	}
	return result, nil
}

func newStore(redisURL string, ttl time.Duration) (store, error) {
	if redisURL == "" {
		return newMemoryStore(), nil
	}
	redisStore, err := newRedisStore(redisURL, ttl)
	if err != nil {
		return nil, fmt.Errorf("invalid redis configuration: %w", err)
	}
	if pingErr := redisStore.client.Ping(context.Background()).Err(); pingErr != nil {
		return nil, fmt.Errorf("redis unavailable: %w", pingErr)
	}
	return redisStore, nil
}

func NewStoreWithFallback(redisURL string, ttl time.Duration) (store, error) {
	resolvedStore, err := newStore(redisURL, ttl)
	if err != nil {
		return newMemoryStore(), err
	}
	return resolvedStore, nil
}
