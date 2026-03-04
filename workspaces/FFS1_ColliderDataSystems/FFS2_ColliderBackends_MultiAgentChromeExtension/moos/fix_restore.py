import re

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

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

text = re.sub(r'func \(manager \*Manager\) restoreSessions\(\) \{.*?\}\n', new_restore, text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
