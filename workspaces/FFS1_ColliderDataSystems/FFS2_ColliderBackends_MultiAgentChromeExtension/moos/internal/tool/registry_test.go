package tool

import (
	"context"
	"database/sql"
	"encoding/json"
	"testing"

	"github.com/collider/moos/internal/container"
)

type fakeContainerStore struct {
	children []container.Record
	records  map[string]container.Record
}

func (store *fakeContainerStore) ListChildren(ctx context.Context, parentURN string) ([]container.Record, error) {
	_ = ctx
	_ = parentURN
	return store.children, nil
}

func (store *fakeContainerStore) GetByURN(ctx context.Context, urn string) (*container.Record, error) {
	_ = ctx
	record, ok := store.records[urn]
	if !ok {
		return nil, container.ErrNotFound
	}
	copyRecord := record
	return &copyRecord, nil
}

func TestRegistryWithContainerStoreListChildren(t *testing.T) {
	store := &fakeContainerStore{children: []container.Record{{URN: "urn:child:1", ParentURN: sql.NullString{String: "urn:root", Valid: true}, Kind: "data"}}}
	registry := NewRegistryWithContainerStore(store)

	result, err := registry.Execute(context.Background(), "list_children", map[string]any{"parent_urn": "urn:root"})
	if err != nil {
		t.Fatalf("expected list_children success: %v", err)
	}
	children, _ := result["children"].([]map[string]any)
	if len(children) != 1 {
		t.Fatalf("expected one child, got %v", result["children"])
	}
}

func TestRegistryWithContainerStoreReadKernel(t *testing.T) {
	store := &fakeContainerStore{records: map[string]container.Record{"urn:node:1": {URN: "urn:node:1", Kind: "tool", KernelJSON: json.RawMessage(`{"name":"node1"}`), Version: 3}}}
	registry := NewRegistryWithContainerStore(store)

	result, err := registry.Execute(context.Background(), "read_kernel", map[string]any{"urn": "urn:node:1"})
	if err != nil {
		t.Fatalf("expected read_kernel success: %v", err)
	}
	if result["version"] != int64(3) {
		t.Fatalf("expected version 3, got %v", result["version"])
	}
	kernel, _ := result["kernel"].(map[string]any)
	if kernel["name"] != "node1" {
		t.Fatalf("expected kernel name node1, got %v", kernel["name"])
	}
}
