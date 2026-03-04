package session

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"
	"sync"
	"time"

	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/model"
	"github.com/collider/moos/internal/morphism"
)

type morphismExecutor interface {
	Apply(ctx context.Context, envelope morphism.Envelope) (int64, error)
}

type containerStore interface {
	ListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error)
	ListChildren(ctx context.Context, parentURN string) ([]container.Record, error)
}

type sessionState struct {
	id           string
	rootURN      string
	createdAt    time.Time
	lastActiveAt time.Time
	messages     []model.Message
	events       chan userEvent
	stopped      chan struct{}
}

type userEvent struct {
	text string
}

type toolDispatcher interface {
	Dispatch(ctx context.Context, sessionID string, call model.ToolCall) (any, error)
}

type Summary struct {
	SessionID    string    `json:"session_id"`
	RootURN      string    `json:"root_urn"`
	CreatedAt    time.Time `json:"created_at"`
	LastActiveAt time.Time `json:"last_active_at"`
}

type Event struct {
	Method string
	Params map[string]any
}

type Manager struct {
	executor     morphismExecutor
	dispatcher   *model.Dispatcher
	logger       *slog.Logger
	ttl          time.Duration
	cleanupEvery time.Duration
	now          func() time.Time

	mu          sync.RWMutex
	sessions    map[string]*sessionState
	dbStore     containerStore
	toolRunner  toolDispatcher
	broadcaster func(sessionID string, event Event)
	activeCache activeStateProjector
	stopCleanup chan struct{}
}

func NewManager(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger) *Manager {
	return NewManagerWithContainerStore(executor, dispatcher, ttl, cleanupEvery, logger, nil)
}

func NewManagerWithContainerStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, dbStore containerStore) *Manager {
	if logger == nil {
		logger = slog.Default()
	}
	if ttl <= 0 {
		ttl = 30 * time.Minute
	}
	if cleanupEvery <= 0 {
		cleanupEvery = time.Minute
	}
	manager := &Manager{
		executor:     executor,
		dispatcher:   dispatcher,
		logger:       logger,
		ttl:          ttl,
		cleanupEvery: cleanupEvery,
		now:          func() time.Time { return time.Now().UTC() },
		sessions:     map[string]*sessionState{},
		dbStore:      dbStore,
		toolRunner:   noopToolDispatcher{},
		activeCache:  nopActiveStateCache{},
		stopCleanup:  make(chan struct{}),
	}
	manager.restoreSessions()
	go manager.cleanupLoop()
	return manager
}

type noopToolDispatcher struct{}

func (runner noopToolDispatcher) Dispatch(ctx context.Context, sessionID string, call model.ToolCall) (any, error) {
	_ = ctx
	return map[string]any{
		"session_id": sessionID,
		"tool":       call.Name,
		"status":     "stubbed",
		"arguments":  call.Arguments,
	}, nil
}

func (manager *Manager) SetToolDispatcher(dispatcher toolDispatcher) {
	if dispatcher == nil {
		dispatcher = noopToolDispatcher{}
	}
	manager.mu.Lock()
	defer manager.mu.Unlock()
	manager.toolRunner = dispatcher
}

func (manager *Manager) SetBroadcaster(broadcaster func(sessionID string, event Event)) {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	manager.broadcaster = broadcaster
}

func (manager *Manager) SetActiveStateCache(cache activeStateProjector) {
	if cache == nil {
		cache = nopActiveStateCache{}
	}
	manager.mu.Lock()
	defer manager.mu.Unlock()
	manager.activeCache = cache
}

func (manager *Manager) Shutdown() {
	close(manager.stopCleanup)
	manager.mu.Lock()
	defer manager.mu.Unlock()
	for _, state := range manager.sessions {
		close(state.stopped)
	}
	manager.sessions = map[string]*sessionState{}
}

func (manager *Manager) Create() (Summary, error) {
	sessionID, err := newSessionID()
	if err != nil {
		return Summary{}, err
	}
	now := manager.now()
	rootURN := fmt.Sprintf("urn:moos:session:%s", sessionID)
	state := &sessionState{
		id:           sessionID,
		rootURN:      rootURN,
		createdAt:    now,
		lastActiveAt: now,
		messages:     []model.Message{},
		events:       make(chan userEvent, 32),
		stopped:      make(chan struct{}),
	}

	manager.mu.Lock()
	manager.sessions[sessionID] = state
	manager.mu.Unlock()

	if manager.executor != nil {
		_, _ = manager.executor.Apply(context.Background(), morphism.Envelope{
			Type:           "ADD",
			ScopeURN:       rootURN,
			IssuedAtUnixMs: now.UnixMilli(),
			Add: &morphism.AddPayload{
				Container: container.Record{
					URN:  rootURN,
					Kind: "SESSION",
				},
			},
		})
	}

	go manager.runSession(state)

	return Summary{SessionID: sessionID, RootURN: rootURN, CreatedAt: now, LastActiveAt: now}, nil
}

func (manager *Manager) Send(sessionID string, text string) error {
	manager.mu.RLock()
	state, ok := manager.sessions[sessionID]
	manager.mu.RUnlock()
	if !ok {
		return fmt.Errorf("session not found")
	}

	select {
	case state.events <- userEvent{text: text}:
		return nil
	default:
		return fmt.Errorf("session queue full")
	}
}

func (manager *Manager) List() []Summary {
	manager.mu.RLock()
	defer manager.mu.RUnlock()
	result := make([]Summary, 0, len(manager.sessions))
	for _, state := range manager.sessions {
		result = append(result, Summary{
			SessionID:    state.id,
			RootURN:      state.rootURN,
			CreatedAt:    state.createdAt,
			LastActiveAt: state.lastActiveAt,
		})
	}
	return result
}

func (manager *Manager) Close(sessionID string) error {
	manager.mu.Lock()
	defer manager.mu.Unlock()
	state, ok := manager.sessions[sessionID]
	if !ok {
		return fmt.Errorf("session not found")
	}
	delete(manager.sessions, sessionID)
	close(state.stopped)
	return nil
}

func (manager *Manager) cleanupLoop() {
	ticker := time.NewTicker(manager.cleanupEvery)
	defer ticker.Stop()
	for {
		select {
		case <-manager.stopCleanup:
			return
		case <-ticker.C:
			manager.cleanupExpired()
		}
	}
}

func (manager *Manager) cleanupExpired() {
	cutoff := manager.now().Add(-manager.ttl)
	manager.mu.Lock()
	defer manager.mu.Unlock()
	for sessionID, state := range manager.sessions {
		if state.lastActiveAt.Before(cutoff) {
			delete(manager.sessions, sessionID)
			close(state.stopped)
		}
	}
}

func (manager *Manager) runSession(state *sessionState) {
	for {
		select {
		case <-state.stopped:
			return
		case event := <-state.events:
			manager.handleUserEvent(state, event)
		}
	}
}

func (manager *Manager) appendMessage(state *sessionState, msg model.Message) {
	state.messages = append(state.messages, msg)
	if manager.executor != nil {
		msgJSON, _ := json.Marshal(msg)
		urnBytes := make([]byte, 8)
		rand.Read(urnBytes)
		msgURN := fmt.Sprintf("urn:moos:message:%s", hex.EncodeToString(urnBytes))
		_, _ = manager.executor.Apply(context.Background(), morphism.Envelope{
			Type:           "ADD",
			ScopeURN:       state.rootURN,
			IssuedAtUnixMs: manager.now().UnixMilli(),
			Add: &morphism.AddPayload{
				Container: container.Record{
					URN:        msgURN,
					ParentURN:  sql.NullString{String: state.rootURN, Valid: true},
					Kind:       "MESSAGE",
					KernelJSON: msgJSON,
				},
			},
		})
	}
}

func (manager *Manager) handleUserEvent(state *sessionState, event userEvent) {
	state.lastActiveAt = manager.now()
	manager.appendMessage(state, model.Message{Role: "user", Content: event.text})
	manager.emit(state.id, Event{Method: "stream.thinking", Params: map[string]any{"session_id": state.id, "text": "processing"}})

	userMorphisms, _ := model.ParseMorphismEnvelopes(event.text)
	userToolCalls := model.ParseToolCalls(event.text)

	if len(userMorphisms) > 0 || len(userToolCalls) > 0 {
		for _, envelope := range userMorphisms {
			if manager.executor == nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": "database not configured"}})
				continue
			}
			if _, applyErr := manager.executor.Apply(context.Background(), envelope); applyErr != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": applyErr.Error()}})
				continue
			}
			_ = manager.activeCache.Set(context.Background(), envelope.ScopeURN, envelope)
			_ = manager.activeCache.Publish(context.Background(), envelope.ScopeURN, envelope)
			manager.emit(state.id, Event{Method: "stream.morphism", Params: map[string]any{"session_id": state.id, "envelope": envelope}})
		}
		for _, toolCall := range userToolCalls {
			output, dispatchErr := manager.toolRunner.Dispatch(context.Background(), state.id, toolCall)
			if dispatchErr != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": dispatchErr.Error()}})
				manager.appendMessage(state, model.Message{Role: "user", Content: fmt.Sprintf("Tool %s failed: %v", toolCall.Name, dispatchErr)})
				continue
			}
			manager.emit(state.id, Event{Method: "stream.tool_result", Params: map[string]any{"session_id": state.id, "tool": toolCall.Name, "output": output}})
			manager.appendMessage(state, model.Message{Role: "user", Content: fmt.Sprintf("Tool %s returned: %v", toolCall.Name, output)})
		}
		manager.emit(state.id, Event{Method: "stream.end", Params: map[string]any{"session_id": state.id, "stop_reason": "end_turn"}})
		return
	}

	for {
		chunks, err := manager.dispatcher.Stream(context.Background(), model.CompletionRequest{
			SessionID: state.id,
			Messages:  append([]model.Message{}, state.messages...),
		})
		if err != nil {
			manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": err.Error()}})
			return
		}

		var fullText strings.Builder
		var allMorphisms []morphism.Envelope
		var allToolCalls []model.ToolCall

		for chunk := range chunks {
			if chunk.Error != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": chunk.Error.Error()}})
				return
			}
			if chunk.Text != "" {
				fullText.WriteString(chunk.Text)
				manager.emit(state.id, Event{Method: "stream.text_delta", Params: map[string]any{"session_id": state.id, "text": chunk.Text}})
			}
			if len(chunk.Morphisms) > 0 {
				allMorphisms = append(allMorphisms, chunk.Morphisms...)
			}
			if len(chunk.ToolCalls) > 0 {
				allToolCalls = append(allToolCalls, chunk.ToolCalls...)
			}
		}

		accumulatedText := fullText.String()

		if accumulatedText != "" {
			manager.appendMessage(state, model.Message{Role: "assistant", Content: accumulatedText})
		}

		for _, envelope := range allMorphisms {
			if manager.executor == nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": "database not configured"}})
				continue
			}
			if _, applyErr := manager.executor.Apply(context.Background(), envelope); applyErr != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": applyErr.Error()}})
				continue
			}
			_ = manager.activeCache.Set(context.Background(), envelope.ScopeURN, envelope)
			_ = manager.activeCache.Publish(context.Background(), envelope.ScopeURN, envelope)
			manager.emit(state.id, Event{Method: "stream.morphism", Params: map[string]any{"session_id": state.id, "envelope": envelope}})
		}

		if len(allToolCalls) == 0 {
			break
		}

		for _, toolCall := range allToolCalls {
			output, dispatchErr := manager.toolRunner.Dispatch(context.Background(), state.id, toolCall)
			if dispatchErr != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": dispatchErr.Error()}})
				manager.appendMessage(state, model.Message{Role: "user", Content: fmt.Sprintf("Tool %s failed: %v", toolCall.Name, dispatchErr)})
				continue
			}
			manager.emit(state.id, Event{Method: "stream.tool_result", Params: map[string]any{"session_id": state.id, "tool": toolCall.Name, "output": output}})
			manager.appendMessage(state, model.Message{Role: "user", Content: fmt.Sprintf("Tool %s returned: %v", toolCall.Name, output)})
		}
	}

	manager.emit(state.id, Event{Method: "stream.end", Params: map[string]any{"session_id": state.id, "stop_reason": "end_turn"}})
}

func (manager *Manager) emit(sessionID string, event Event) {
	manager.mu.RLock()
	broadcaster := manager.broadcaster
	manager.mu.RUnlock()
	if broadcaster != nil {
		broadcaster(sessionID, event)
	}
}

func newSessionID() (string, error) {
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return "s_" + hex.EncodeToString(bytes), nil
}

func (manager *Manager) restoreSessions() {
	if manager.dbStore == nil {
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	sessions, err := manager.dbStore.ListByKind(ctx, "SESSION", 50)
	if err != nil {
		manager.logger.Warn("failed to restore sessions from db", "error", err)
		return
	}

	for _, rec := range sessions {
		sessionID := strings.TrimPrefix(rec.URN, "urn:moos:session:")
		state := &sessionState{
			id:           sessionID,
			rootURN:      rec.URN,
			createdAt:    manager.now(),
			lastActiveAt: manager.now(),
			messages:     []model.Message{},
			events:       make(chan userEvent, 32),
			stopped:      make(chan struct{}),
		}

		children, childErr := manager.dbStore.ListChildren(ctx, rec.URN)
		if childErr == nil {
			for _, child := range children {
				if child.Kind == "MESSAGE" {
					var msg model.Message
					if unmarshalErr := json.Unmarshal(child.KernelJSON, &msg); unmarshalErr == nil {
						state.messages = append(state.messages, msg)
					}
				}
			}
		}

		manager.sessions[sessionID] = state
		go manager.runSession(state)
	}
}
