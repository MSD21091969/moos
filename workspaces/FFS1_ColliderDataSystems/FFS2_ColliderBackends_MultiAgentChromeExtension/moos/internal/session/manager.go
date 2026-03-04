package session

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"github.com/collider/moos/internal/model"
	"github.com/collider/moos/internal/morphism"
)

type morphismExecutor interface {
	Apply(ctx context.Context, envelope morphism.Envelope) (int64, error)
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
	store       store
	toolRunner  toolDispatcher
	broadcaster func(sessionID string, event Event)
	stopCleanup chan struct{}
}

func NewManager(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger) *Manager {
	return NewManagerWithStore(executor, dispatcher, ttl, cleanupEvery, logger, nil)
}

func NewManagerWithStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, sessionStore store) *Manager {
	if logger == nil {
		logger = slog.Default()
	}
	if ttl <= 0 {
		ttl = 30 * time.Minute
	}
	if cleanupEvery <= 0 {
		cleanupEvery = time.Minute
	}
	if sessionStore == nil {
		sessionStore = newMemoryStore()
	}
	manager := &Manager{
		executor:     executor,
		dispatcher:   dispatcher,
		logger:       logger,
		ttl:          ttl,
		cleanupEvery: cleanupEvery,
		now:          func() time.Time { return time.Now().UTC() },
		sessions:     map[string]*sessionState{},
		store:        sessionStore,
		toolRunner:   noopToolDispatcher{},
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
	_ = manager.persistState(state)

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
	_ = manager.store.Delete(context.Background(), sessionID)
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
			_ = manager.store.Delete(context.Background(), sessionID)
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

func (manager *Manager) handleUserEvent(state *sessionState, event userEvent) {
	state.lastActiveAt = manager.now()
	state.messages = append(state.messages, model.Message{Role: "user", Content: event.text})
	_ = manager.persistState(state)
	manager.emit(state.id, Event{Method: "stream.thinking", Params: map[string]any{"session_id": state.id, "text": "processing"}})

	for {
		result, err := manager.dispatcher.Complete(context.Background(), model.CompletionRequest{
			SessionID: state.id,
			Messages:  append([]model.Message{}, state.messages...),
		})
		if err != nil {
			manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": err.Error()}})
			return
		}

		if result.Text != "" {
			state.messages = append(state.messages, model.Message{Role: "assistant", Content: result.Text})
			_ = manager.persistState(state)
			manager.emit(state.id, Event{Method: "stream.text_delta", Params: map[string]any{"session_id": state.id, "text": result.Text}})
		}

		for _, envelope := range result.Morphisms {
			if manager.executor == nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": "database not configured"}})
				continue
			}
			if _, applyErr := manager.executor.Apply(context.Background(), envelope); applyErr != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": applyErr.Error()}})
				continue
			}
			manager.emit(state.id, Event{Method: "stream.morphism", Params: map[string]any{"session_id": state.id, "envelope": envelope}})
		}

		if len(result.ToolCalls) == 0 {
			break
		}

		for _, toolCall := range result.ToolCalls {
			output, dispatchErr := manager.toolRunner.Dispatch(context.Background(), state.id, toolCall)
			if dispatchErr != nil {
				manager.emit(state.id, Event{Method: "stream.error", Params: map[string]any{"session_id": state.id, "error": dispatchErr.Error()}})
				state.messages = append(state.messages, model.Message{Role: "user", Content: fmt.Sprintf("Tool %s failed: %v", toolCall.Name, dispatchErr)})
				continue
			}
			manager.emit(state.id, Event{Method: "stream.tool_result", Params: map[string]any{"session_id": state.id, "tool": toolCall.Name, "output": output}})
			state.messages = append(state.messages, model.Message{Role: "user", Content: fmt.Sprintf("Tool %s returned: %v", toolCall.Name, output)})
		}
		_ = manager.persistState(state)
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

func (manager *Manager) persistState(state *sessionState) error {
	if manager.store == nil {
		return nil
	}
	snapshot := sessionSnapshot{
		Summary: Summary{
			SessionID:    state.id,
			RootURN:      state.rootURN,
			CreatedAt:    state.createdAt,
			LastActiveAt: state.lastActiveAt,
		},
		Messages: append([]model.Message{}, state.messages...),
	}
	return manager.store.Save(context.Background(), snapshot)
}

func (manager *Manager) restoreSessions() {
	if manager.store == nil {
		return
	}
	snapshots, err := manager.store.List(context.Background())
	if err != nil {
		manager.logger.Warn("failed to restore sessions", "error", err)
		return
	}
	for _, snapshot := range snapshots {
		if snapshot.Summary.SessionID == "" {
			continue
		}
		state := &sessionState{
			id:           snapshot.Summary.SessionID,
			rootURN:      snapshot.Summary.RootURN,
			createdAt:    snapshot.Summary.CreatedAt,
			lastActiveAt: snapshot.Summary.LastActiveAt,
			messages:     append([]model.Message{}, snapshot.Messages...),
			events:       make(chan userEvent, 32),
			stopped:      make(chan struct{}),
		}
		manager.sessions[state.id] = state
		go manager.runSession(state)
	}
}
