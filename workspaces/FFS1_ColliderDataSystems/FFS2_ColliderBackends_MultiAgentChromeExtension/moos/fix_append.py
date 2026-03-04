import re

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

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
}'''

text = re.sub(r'func \(manager \*Manager\) appendMessage\(state \*sessionState, msg model\.Message\) \{.*?\}\n', new_append + '\n', text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
