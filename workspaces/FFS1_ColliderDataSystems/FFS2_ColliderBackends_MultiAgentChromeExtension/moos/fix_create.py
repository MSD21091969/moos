import re

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

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
\t\tSessionID:    id,
\t\tRootURN:      rootURN,
\t\tCreatedAt:    state.createdAt,
\t\tLastActiveAt: state.lastActiveAt,
\t}, nil
}
'''
text = re.sub(r"func \(manager \*Manager\) Create\(\) \(Summary, error\) \{.*?\}\n\}\n", create_func, text, flags=re.DOTALL)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
