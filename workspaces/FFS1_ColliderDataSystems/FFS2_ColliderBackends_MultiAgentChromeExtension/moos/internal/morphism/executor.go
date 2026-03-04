package morphism

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/collider/moos/internal/container"
)

var ErrInvalidEnvelope = errors.New("invalid morphism envelope")

type store interface {
	Create(ctx context.Context, record container.Record) error
	MutateKernel(ctx context.Context, urn string, expectedVersion int64, kernelJSON json.RawMessage) (int64, error)
	Link(ctx context.Context, wire container.WireRecord) error
	Unlink(ctx context.Context, wire container.WireRecord) error
	AppendMorphismLog(ctx context.Context, record container.MorphismLogRecord) error
}

type Executor struct {
	store    store
	actorURN string
	now      func() time.Time
}

type Envelope struct {
	ID             string         `json:"id"`
	Type           string         `json:"type"`
	ActorURN       string         `json:"actor_urn"`
	ScopeURN       string         `json:"scope_urn"`
	IssuedAtUnixMs int64          `json:"issued_at_unix_ms"`
	Add            *AddPayload    `json:"add,omitempty"`
	Link           *LinkPayload   `json:"link,omitempty"`
	Mutate         *MutatePayload `json:"mutate,omitempty"`
	Unlink         *UnlinkPayload `json:"unlink,omitempty"`
}

type AddPayload struct {
	Container container.Record `json:"container"`
}

type LinkPayload struct {
	Wire container.WireRecord `json:"wire"`
}

type MutatePayload struct {
	URN             string          `json:"urn"`
	ExpectedVersion int64           `json:"expected_version"`
	KernelJSON      json.RawMessage `json:"kernel_json"`
}

type UnlinkPayload struct {
	Wire container.WireRecord `json:"wire"`
}

func NewExecutor(store store, actorURN string) *Executor {
	return &Executor{store: store, actorURN: actorURN, now: func() time.Time { return time.Now().UTC() }}
}

func (executor *Executor) Apply(ctx context.Context, envelope Envelope) (int64, error) {
	switch envelope.Type {
	case "ADD":
		if envelope.Add == nil {
			return 0, ErrInvalidEnvelope
		}
		return 0, executor.Add(ctx, envelope.Add.Container)
	case "LINK":
		if envelope.Link == nil {
			return 0, ErrInvalidEnvelope
		}
		return 0, executor.Link(ctx, envelope.Link.Wire)
	case "MUTATE":
		if envelope.Mutate == nil {
			return 0, ErrInvalidEnvelope
		}
		return executor.Mutate(ctx, envelope.Mutate.URN, envelope.Mutate.ExpectedVersion, envelope.Mutate.KernelJSON)
	case "UNLINK":
		if envelope.Unlink == nil {
			return 0, ErrInvalidEnvelope
		}
		return 0, executor.Unlink(ctx, envelope.Unlink.Wire)
	default:
		return 0, ErrInvalidEnvelope
	}
}

func (executor *Executor) Add(ctx context.Context, record container.Record) error {
	if err := executor.store.Create(ctx, record); err != nil {
		return err
	}
	return executor.append(ctx, "ADD", record.URN, nil, map[string]any{
		"urn":              record.URN,
		"parent_urn":       record.ParentURN.String,
		"kind":             record.Kind,
		"interface_json":   record.InterfaceJSON,
		"kernel_json":      record.KernelJSON,
		"permissions_json": record.PermissionsJSON,
	})
}

func (executor *Executor) Link(ctx context.Context, wire container.WireRecord) error {
	if err := executor.store.Link(ctx, wire); err != nil {
		return err
	}
	return executor.append(ctx, "LINK", wire.FromContainerURN, nil, map[string]any{
		"from_urn":      wire.FromContainerURN,
		"from_port":     wire.FromPort,
		"to_urn":        wire.ToContainerURN,
		"to_port":       wire.ToPort,
		"metadata_json": wire.MetadataJSON,
	})
}

func (executor *Executor) Mutate(ctx context.Context, urn string, expectedVersion int64, kernelJSON json.RawMessage) (int64, error) {
	nextVersion, err := executor.store.MutateKernel(ctx, urn, expectedVersion, kernelJSON)
	if err != nil {
		return nextVersion, err
	}
	if appendErr := executor.append(ctx, "MUTATE", urn, &expectedVersion, map[string]any{
		"urn":              urn,
		"expected_version": expectedVersion,
		"kernel_json":      kernelJSON,
		"next_version":     nextVersion,
	}); appendErr != nil {
		return 0, appendErr
	}
	return nextVersion, nil
}

func (executor *Executor) Unlink(ctx context.Context, wire container.WireRecord) error {
	if err := executor.store.Unlink(ctx, wire); err != nil {
		return err
	}
	return executor.append(ctx, "UNLINK", wire.FromContainerURN, nil, map[string]any{
		"from_urn":      wire.FromContainerURN,
		"from_port":     wire.FromPort,
		"to_urn":        wire.ToContainerURN,
		"to_port":       wire.ToPort,
		"metadata_json": wire.MetadataJSON,
	})
}

func (executor *Executor) append(ctx context.Context, morphismType string, scopeURN string, expectedVersion *int64, payload map[string]any) error {
	payloadJSON, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	return executor.store.AppendMorphismLog(ctx, container.MorphismLogRecord{
		Type:            morphismType,
		ActorURN:        executor.actorURN,
		ScopeURN:        scopeURN,
		ExpectedVersion: expectedVersion,
		PayloadJSON:     payloadJSON,
		IssuedAt:        executor.now(),
	})
}
