package session

import (
	"context"
	"sync"
	"time"

	"github.com/collider/moos/internal/model"
)

type sessionSnapshot struct {
	Summary  Summary
	Messages []model.Message
}

type store interface {
	Save(ctx context.Context, snapshot sessionSnapshot) error
	List(ctx context.Context) ([]sessionSnapshot, error)
	Delete(ctx context.Context, sessionID string) error
}

type memoryStore struct {
	mu        sync.RWMutex
	snapshots map[string]sessionSnapshot
}

func newMemoryStore() store {
	return &memoryStore{snapshots: map[string]sessionSnapshot{}}
}

func (store *memoryStore) Save(ctx context.Context, snapshot sessionSnapshot) error {
	_ = ctx
	store.mu.Lock()
	defer store.mu.Unlock()
	store.snapshots[snapshot.Summary.SessionID] = cloneSnapshot(snapshot)
	return nil
}

func (store *memoryStore) List(ctx context.Context) ([]sessionSnapshot, error) {
	_ = ctx
	store.mu.RLock()
	defer store.mu.RUnlock()
	result := make([]sessionSnapshot, 0, len(store.snapshots))
	for _, snapshot := range store.snapshots {
		result = append(result, cloneSnapshot(snapshot))
	}
	return result, nil
}

func (store *memoryStore) Delete(ctx context.Context, sessionID string) error {
	_ = ctx
	store.mu.Lock()
	defer store.mu.Unlock()
	delete(store.snapshots, sessionID)
	return nil
}

func cloneSnapshot(snapshot sessionSnapshot) sessionSnapshot {
	clonedMessages := make([]model.Message, len(snapshot.Messages))
	copy(clonedMessages, snapshot.Messages)
	return sessionSnapshot{
		Summary: Summary{
			SessionID:    snapshot.Summary.SessionID,
			RootURN:      snapshot.Summary.RootURN,
			CreatedAt:    snapshot.Summary.CreatedAt,
			LastActiveAt: snapshot.Summary.LastActiveAt,
		},
		Messages: clonedMessages,
	}
}

func NewStoreWithFallback(redisURL string, ttl time.Duration) (store, error) {
	_ = redisURL
	_ = ttl
	return newMemoryStore(), nil
}
