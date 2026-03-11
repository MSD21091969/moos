package shell

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"moos/platform/kernel/internal/cat"
)

// LogStore is a JSONL append-only file store for the morphism log.
// Each line is one JSON-encoded PersistedEnvelope.
type LogStore struct {
	path string
}

// NewLogStore creates a LogStore at the given file path.
// Creates the parent directory if it doesn't exist.
func NewLogStore(path string) (*LogStore, error) {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, fmt.Errorf("creating log directory: %w", err)
	}
	return &LogStore{path: path}, nil
}

func (s *LogStore) Append(entries []cat.PersistedEnvelope) error {
	f, err := os.OpenFile(s.path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return fmt.Errorf("opening log file: %w", err)
	}
	defer f.Close()

	enc := json.NewEncoder(f)
	for _, entry := range entries {
		if err := enc.Encode(entry); err != nil {
			return fmt.Errorf("encoding log entry: %w", err)
		}
	}
	return nil
}

func (s *LogStore) ReadAll() ([]cat.PersistedEnvelope, error) {
	f, err := os.Open(s.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil // empty log → empty state
		}
		return nil, fmt.Errorf("opening log file: %w", err)
	}
	defer f.Close()

	var entries []cat.PersistedEnvelope
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 1024*1024), 10*1024*1024) // 10MB max line
	lineNum := 0
	for scanner.Scan() {
		lineNum++
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var entry cat.PersistedEnvelope
		if err := json.Unmarshal(line, &entry); err != nil {
			return nil, fmt.Errorf("parsing log line %d: %w", lineNum, err)
		}
		entries = append(entries, entry)
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("scanning log file: %w", err)
	}
	return entries, nil
}
