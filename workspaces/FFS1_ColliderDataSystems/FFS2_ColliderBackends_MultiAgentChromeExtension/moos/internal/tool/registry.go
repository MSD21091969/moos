package tool

import (
	"context"
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"sync"

	"github.com/collider/moos/internal/container"
)

type Handler func(ctx context.Context, arguments map[string]any) (map[string]any, error)

type Definition struct {
	Name        string            `json:"name"`
	Description string            `json:"description"`
	Schema      map[string]any    `json:"schema,omitempty"`
	Metadata    map[string]string `json:"metadata,omitempty"`
}

type Registry struct {
	mu          sync.RWMutex
	definitions map[string]Definition
	handlers    map[string]Handler
}

type containerStore interface {
	ListChildren(ctx context.Context, parentURN string) ([]container.Record, error)
	GetByURN(ctx context.Context, urn string) (*container.Record, error)
}

func NewRegistry() *Registry {
	registry := &Registry{
		definitions: map[string]Definition{},
		handlers:    map[string]Handler{},
	}
	registry.MustRegister(Definition{Name: "echo", Description: "Echo back provided arguments"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = ctx
		return map[string]any{"echo": arguments}, nil
	})
	registry.MustRegister(Definition{Name: "list_children", Description: "List direct children for a parent container URN"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = ctx
		return map[string]any{"children": []any{}, "source": "stub", "arguments": arguments}, nil
	})
	registry.MustRegister(Definition{Name: "read_kernel", Description: "Read kernel JSON for a container URN"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = ctx
		return map[string]any{"kernel": map[string]any{}, "source": "stub", "arguments": arguments}, nil
	})
	registry.MustRegister(Definition{Name: "search", Description: "Search containers (baseline keyword search placeholder)"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		_ = ctx
		query, _ := arguments["query"].(string)
		return map[string]any{"query": strings.TrimSpace(query), "matches": []any{}, "source": "stub"}, nil
	})
	return registry
}

func NewRegistryWithContainerStore(store containerStore) *Registry {
	registry := NewRegistry()
	if store == nil {
		return registry
	}

	registry.MustRegister(Definition{Name: "list_children", Description: "List direct children for a parent container URN"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		parentURN, _ := arguments["parent_urn"].(string)
		parentURN = strings.TrimSpace(parentURN)
		if parentURN == "" {
			return nil, fmt.Errorf("parent_urn is required")
		}
		records, err := store.ListChildren(ctx, parentURN)
		if err != nil {
			return nil, err
		}
		children := make([]map[string]any, 0, len(records))
		for _, record := range records {
			children = append(children, map[string]any{
				"urn":  record.URN,
				"kind": record.Kind,
			})
		}
		return map[string]any{"parent_urn": parentURN, "children": children}, nil
	})

	registry.MustRegister(Definition{Name: "read_kernel", Description: "Read kernel JSON for a container URN"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		urn, _ := arguments["urn"].(string)
		urn = strings.TrimSpace(urn)
		if urn == "" {
			return nil, fmt.Errorf("urn is required")
		}
		record, err := store.GetByURN(ctx, urn)
		if err != nil {
			return nil, err
		}
		kernel := map[string]any{}
		if len(record.KernelJSON) > 0 {
			if err := json.Unmarshal(record.KernelJSON, &kernel); err != nil {
				return nil, err
			}
		}
		return map[string]any{"urn": urn, "kernel": kernel, "version": record.Version}, nil
	})

	registry.MustRegister(Definition{Name: "search", Description: "Search containers (baseline keyword search over direct children URNs)"}, func(ctx context.Context, arguments map[string]any) (map[string]any, error) {
		parentURN, _ := arguments["parent_urn"].(string)
		query, _ := arguments["query"].(string)
		parentURN = strings.TrimSpace(parentURN)
		query = strings.ToLower(strings.TrimSpace(query))
		if parentURN == "" || query == "" {
			return nil, fmt.Errorf("parent_urn and query are required")
		}
		records, err := store.ListChildren(ctx, parentURN)
		if err != nil {
			return nil, err
		}
		matches := make([]map[string]any, 0)
		for _, record := range records {
			if strings.Contains(strings.ToLower(record.URN), query) || strings.Contains(strings.ToLower(record.Kind), query) {
				matches = append(matches, map[string]any{"urn": record.URN, "kind": record.Kind})
			}
		}
		return map[string]any{"parent_urn": parentURN, "query": query, "matches": matches}, nil
	})

	return registry
}

func (registry *Registry) MustRegister(definition Definition, handler Handler) {
	if err := registry.Register(definition, handler); err != nil {
		panic(err)
	}
}

func (registry *Registry) Register(definition Definition, handler Handler) error {
	if definition.Name == "" {
		return fmt.Errorf("tool name is required")
	}
	if handler == nil {
		return fmt.Errorf("tool handler is required")
	}
	registry.mu.Lock()
	defer registry.mu.Unlock()
	registry.definitions[definition.Name] = definition
	registry.handlers[definition.Name] = handler
	return nil
}

func (registry *Registry) List() []Definition {
	registry.mu.RLock()
	defer registry.mu.RUnlock()
	result := make([]Definition, 0, len(registry.definitions))
	for _, definition := range registry.definitions {
		result = append(result, definition)
	}
	sort.Slice(result, func(i, j int) bool {
		return result[i].Name < result[j].Name
	})
	return result
}

func (registry *Registry) Execute(ctx context.Context, name string, arguments map[string]any) (map[string]any, error) {
	registry.mu.RLock()
	handler, ok := registry.handlers[name]
	registry.mu.RUnlock()
	if !ok {
		return nil, fmt.Errorf("tool not found: %s", name)
	}
	return handler(ctx, arguments)
}
