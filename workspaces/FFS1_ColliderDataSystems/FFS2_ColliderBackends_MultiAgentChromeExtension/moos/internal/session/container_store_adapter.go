package session

import (
	"context"
	"encoding/json"
	"log/slog"
	"strings"
	"time"

	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/model"
)

type containerStore interface {
	ListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error)
	ListChildren(ctx context.Context, parentURN string) ([]container.Record, error)
}

type containerSessionStore struct {
	db containerStore
}

func NewManagerWithContainerStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, dbStore containerStore) *Manager {
	if dbStore == nil {
		return NewManagerWithStore(executor, dispatcher, ttl, cleanupEvery, logger, nil)
	}
	return NewManagerWithStore(executor, dispatcher, ttl, cleanupEvery, logger, &containerSessionStore{db: dbStore})
}

func (store *containerSessionStore) Save(ctx context.Context, snapshot sessionSnapshot) error {
	_ = ctx
	_ = snapshot
	return nil
}

func (store *containerSessionStore) List(ctx context.Context) ([]sessionSnapshot, error) {
	records, err := store.db.ListByKind(ctx, "SESSION", 100)
	if err != nil {
		return nil, err
	}

	result := make([]sessionSnapshot, 0, len(records))
	for _, record := range records {
		if !strings.HasPrefix(record.URN, "urn:moos:session:") {
			continue
		}
		sessionID := strings.TrimPrefix(record.URN, "urn:moos:session:")
		messages := make([]model.Message, 0)
		children, childErr := store.db.ListChildren(ctx, record.URN)
		if childErr == nil {
			for _, child := range children {
				if child.Kind != "MESSAGE" || len(child.KernelJSON) == 0 {
					continue
				}
				var message model.Message
				if unmarshalErr := json.Unmarshal(child.KernelJSON, &message); unmarshalErr != nil {
					continue
				}
				messages = append(messages, message)
			}
		}
		result = append(result, sessionSnapshot{
			Summary: Summary{
				SessionID:    sessionID,
				RootURN:      record.URN,
				CreatedAt:    time.Now().UTC(),
				LastActiveAt: time.Now().UTC(),
			},
			Messages: messages,
		})
	}

	return result, nil
}

func (store *containerSessionStore) Delete(ctx context.Context, sessionID string) error {
	_ = ctx
	_ = sessionID
	return nil
}
