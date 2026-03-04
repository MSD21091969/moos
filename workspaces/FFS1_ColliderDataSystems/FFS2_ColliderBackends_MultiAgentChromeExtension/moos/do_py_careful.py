import re

path = 'internal/session/manager.go'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. ADD containerStore next to morphismExecutor
text = text.replace(
'''type morphismExecutor interface {
\tApply(ctx context.Context, envelope morphism.Envelope) (int64, error)
}''',
'''type morphismExecutor interface {
\tApply(ctx context.Context, envelope morphism.Envelope) (int64, error)
}

type containerStore interface {
\tListByKind(ctx context.Context, kind string, limit int) ([]container.Record, error)
\tListChildren(ctx context.Context, parentURN string) ([]container.Record, error)
}'''
)

# 2. Add dbStore to Manager struct
text = text.replace(
'''\tstore       store''',
'''\t//store     store (removed)
\tdbStore     containerStore'''
)

# 3. Rename NewManagerWithStore and fix dbStore init
text = text.replace(
'''func NewManagerWithStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, sessionStore store) *Manager {''',
'''func NewManagerWithContainerStore(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger, dbStore containerStore) *Manager {'''
)
text = text.replace(
'''func NewManager(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger) *Manager {
\treturn NewManagerWithStore(executor, dispatcher, ttl, cleanupEvery, logger, nil)
}''',
'''func NewManager(executor morphismExecutor, dispatcher *model.Dispatcher, ttl time.Duration, cleanupEvery time.Duration, logger *slog.Logger) *Manager {
\treturn NewManagerWithContainerStore(executor, dispatcher, ttl, cleanupEvery, logger, nil)
}'''
)

text = text.replace("store:       sessionStore,", "dbStore:     dbStore,")

# remove newMemoryStore()
text = re.sub(r'\tif m\.store == nil \{\n\t\tm\.store = newMemoryStore\(\)\n\t\}\n', '', text)

# 4. Remove persistState entirely
text = re.sub(r'func \(manager \*Manager\) persistState\(state \*sessionState\) \{.*?\}\n\n', '', text, flags=re.DOTALL)
text = text.replace("\tmanager.persistState(state)\n", "")

# 5. Fix references to manager.store inside List(), Create(), Close(), cleanupExpired()
# In Create: remove `_ = manager.store.Set(...)`
text = re.sub(r'_ = manager\.store\.Delete\(context\.Background\(\), sessionID\)', '', text)

# For List() which loops over manager.store.List()
list_func = '''func (manager *Manager) List() []Summary {
\tmanager.mu.RLock()
\tdefer manager.mu.RUnlock()

\tvar summaries []Summary
\tfor id, state := range manager.sessions {
\t\tsummaries = append(summaries, Summary{
\t\t\tSessionID:    id,
\t\t\tRootURN:      state.rootURN,
\t\t\tCreatedAt:    state.createdAt,
\t\t\tLastActiveAt: state.lastActiveAt,
\t\t})
\t}
\treturn summaries
}'''
text = re.sub(r'func \(manager \*Manager\) List\(\) \[\]Summary \{.*?\}\n', list_func + '\n', text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
