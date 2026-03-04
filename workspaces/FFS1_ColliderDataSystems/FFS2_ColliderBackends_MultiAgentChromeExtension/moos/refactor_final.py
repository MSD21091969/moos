import sys

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if skip:
        # Stop skipping if we hit the end of a block we wanted to remove
        if line.startswith("}") and skip_until_brace:
            skip = False
            skip_until_brace = False
        continue

    if line.startswith("type store interface {"):
        new_lines.append("type containerStore interface {\n")
        new_lines.append("\tListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error)\n")
        new_lines.append("\tListChildren(ctx context.Context, parentURN string) ([]container.Record, error)\n")
        new_lines.append("}\n")
        skip = True
        skip_until_brace = True
        continue
    
    if line.startswith("\tactiveStore store"):
        new_lines.append("\tdbStore containerStore\n")
        continue

    if line.startswith("func NewManagerWithStore("):
        new_lines.append("func NewManagerWithContainerStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, dbStore containerStore) *Manager {\n")
        continue

    if line.strip() == "activeStore:  activeStore,":
        new_lines.append("\t\tdbStore: dbStore,\n")
        continue

    if line.startswith("func (manager *Manager) persistState("):
        skip = True
        skip_until_brace = True
        continue
        
    if "manager.persistState(state)" in line:
        continue # Remove this line

    if line.startswith("func (manager *Manager) Create() (Summary, error) {"):
        new_lines.append('''func (manager *Manager) Create() (Summary, error) {
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
\t\tCreatedAt:    state.createdAt,
\t\tLastActiveAt: state.lastActiveAt,
\t}, nil
}
''')
        skip = True
        skip_until_brace = True
        continue
    
    if line.startswith("func (manager *Manager) appendMessage("):
        new_lines.append('''func (manager *Manager) appendMessage(state *sessionState, msg model.Message) {
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
''')
        skip = True
        skip_until_brace = True
        continue

    if line.startswith("func (manager *Manager) restoreSessions() {"):
        new_lines.append('''func (manager *Manager) restoreSessions() {
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
''')
        skip = True
        skip_until_brace = True
        continue

    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("refactored successfully")
