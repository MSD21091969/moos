package shell

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"

	"moos/platform/kernel/internal/core"
)

type LogStore struct {
	Path string
}

func (store LogStore) Append(entry core.PersistedEnvelope) error {
	return store.AppendBatch([]core.PersistedEnvelope{entry})
}

func (store LogStore) AppendBatch(entries []core.PersistedEnvelope) error {
	if len(entries) == 0 {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(store.Path), 0o755); err != nil {
		return err
	}
	file, err := os.OpenFile(store.Path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return err
	}
	defer file.Close()

	for _, entry := range entries {
		encoded, err := json.Marshal(entry)
		if err != nil {
			return err
		}
		if _, err := file.Write(append(encoded, '\n')); err != nil {
			return err
		}
	}
	return nil
}

func (store LogStore) Load() ([]core.PersistedEnvelope, error) {
	file, err := os.Open(store.Path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return nil, nil
		}
		return nil, err
	}
	defer file.Close()

	entries := []core.PersistedEnvelope{}
	scanner := bufio.NewScanner(file)
	lineNumber := 0
	for scanner.Scan() {
		lineNumber++
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var entry core.PersistedEnvelope
		if err := json.Unmarshal(line, &entry); err != nil {
			return nil, fmt.Errorf("invalid morphism log line %d: %w", lineNumber, err)
		}
		entries = append(entries, entry)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return entries, nil
}
