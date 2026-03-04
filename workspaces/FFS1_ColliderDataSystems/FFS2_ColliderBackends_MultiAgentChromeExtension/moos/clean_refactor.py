import os
import re

path = r"internal/session/manager.go"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Interface for DB store
text = text.replace(
    '''type store interface {
\tGet(id string) ([]model.Message, bool)
\tSet(id string, messages []model.Message)
\tList() []sessionSnapshot
\tDelete(id string)
}''',
    '''type containerStore interface {
\tListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error)
\tListChildren(ctx context.Context, parentURN string) ([]container.Record, error)
}'''
)

# 2. Add Manager.dbStore inside struct Manager
text = text.replace(
    '''\tdispatcher  *model.Dispatcher
\tactiveStore store''',
    '''\tdispatcher   *model.Dispatcher
\tdbStore      containerStore'''
)

# 3. Rename NewManagerWithStore -> NewManagerWithContainerStore
text = text.replace(
    "func NewManagerWithStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, activeStore store) *Manager {",
    "func NewManagerWithContainerStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, dbStore containerStore) *Manager {"
)
text = text.replace("activeStore:  activeStore,", "dbStore:      dbStore,")

# 4. Remove persistState
text = re.sub(r"func \(manager \*Manager\) persistState.*?\}\n\n", "", text, flags=re.DOTALL)

# 5. Create
create_func = '''func (manager *Manager) Create() (Summary, error) {
\tidBytes := make([]byte, 16)
\trand.Read(idBytes)
\tid := hex.EncodeToString(idBytes)

\trootURN := fmt.Sprintf("urn:moos:session:%s", id)

\tstate := &sessionState{
\t\tid:           id,
\t\trootURN:      rootURN,
\t\tcreatedAt:    manager.now(),
\t\tlastActiveAt: manager.now(),
\t\tmessages:     []model.Message{},
\t\tevents:       make(chan userEvent, 32),
\t\tstopped:      make(chan struct{}),
\t}

\tmanager.mu.Lock()
\tmanager.sessions[id] = state
\tmanager.mu.Unlock()

\tif manager.executor != nil {
\t\t_, _ = manager.executor.Apply(context.Background(), morphism.Envelope{
\t\t\tType:           "ADD",
\t\t\tScopeURN:       rootURN,
\t\t\tIssuedAtUnixMs: manager.now().UnixMilli(),
\t\t\tAdd: &morphism.AddPayload{
\t\t\t\tContainer: container.Record{
\t\t\t\t\tURN:  rootURN,
\t\t\t\t\tKind: "SESSION",
\t\t\t\t},
\t\t\t},
\t\t})
\t}

\tgo manager.runSession(state)

\treturn Summary{
\t\tID:           id,
\t\tMessageCount: 0,
\t\tCreatedAt:    state.createdAt,
\t\tLastActiveAt: state.lastActiveAt,
\t}, nil
}
'''
text = re.sub(r"func \(manager \*Manager\) Create\(\) \(Summary, error\) \{.*?\n\}\n", create_func, text, flags=re.DOTALL)

# 6. appendMessage and handleUserEvent adjustments
new_append = '''func (manager *Manager) appendMessage(state *sessionState, msg model.Message) {
\tstate.messages = append(state.messages, msg)

\tif manager.executor != nil {
\t\tmsgJSON, _ := json.Marshal(msg)
\t\turnBytes := make([]byte, 8)
\t\trand.Read(urnBytes)
\t\tmsgURN := fmt.Sprintf("urn:moos:message:%s", hex.EncodeToString(urnBytes))
\t\t_, _ = manager.executor.Apply(context.Background(), morphism.Envelope{
\t\t\tType:           "ADD",
\t\t\tScopeURN:       state.rootURN,
\t\t\tIssuedAtUnixMs: manager.now().UnixMilli(),
\t\t\tAdd: &morphism.AddPayload{
\t\t\t\tContainer: container.Record{
\t\t\t\t\tURN:        msgURN,
\t\t\t\t\tParentURN:  sql.NullString{String: state.rootURN, Valid: true},
\t\t\t\t\tKind:       "MESSAGE",
\t\t\t\t\tKernelJSON: msgJSON,
\t\t\t\t},
\t\t\t},
\t\t})
\t}
}
'''

text = text.replace("manager.persistState(state)", "")

text = re.sub(r"func \(manager \*Manager\) appendMessage\(.*?\}\n", new_append, text, flags=re.DOTALL)

# 7. restoreSessions
new_restore = '''func (manager *Manager) restoreSessions() {
\tif manager.dbStore == nil {
\t\treturn
\t}
\tctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
\tdefer cancel()

\tsessions, err := manager.dbStore.ListByKind(ctx, "SESSION", 50)
\tif err != nil {
\t\tmanager.logger.Warn("failed to restore sessions from db", "error", err)
\t\treturn
\t}

\tfor _, rec := range sessions {
\t\tsessionID := strings.TrimPrefix(rec.URN, "urn:moos:session:")
\t\tstate := &sessionState{
\t\t\tid:           sessionID,
\t\t\trootURN:      rec.URN,
\t\t\tcreatedAt:    manager.now(),
\t\t\tlastActiveAt: manager.now(),
\t\t\tmessages:     []model.Message{},
\t\t\tevents:       make(chan userEvent, 32),
\t\t\tstopped:      make(chan struct{}),
\t\t}
\t\t
\t\tchildren, childErr := manager.dbStore.ListChildren(ctx, rec.URN)
\t\tif childErr == nil {
\t\t\tfor _, child := range children {
\t\t\t\tif child.Kind == "MESSAGE" {
\t\t\t\t\tvar msg model.Message
\t\t\t\t\tif unmarshalErr := json.Unmarshal(child.KernelJSON, &msg); unmarshalErr == nil {
\t\t\t\t\t\tstate.messages = append(state.messages, msg)
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}

\t\tmanager.sessions[sessionID] = state
\t\tgo manager.runSession(state)
\t}
}
'''
text = re.sub(r"func \(manager \*Manager\) restoreSessions\(\) \{.*?\n\}\n", new_restore, text, flags=re.DOTALL)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("clean refactor done")
