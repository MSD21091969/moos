package core

import "time"

type URN string
type Kind string
type Port string
type Stratum string
type MorphismType string

const (
	StratumAuthored     Stratum = "S0"
	StratumValidated    Stratum = "S1"
	StratumMaterialized Stratum = "S2"
	StratumEvaluated    Stratum = "S3"
	StratumProjected    Stratum = "S4"
)

const (
	MorphismAdd    MorphismType = "ADD"
	MorphismLink   MorphismType = "LINK"
	MorphismMutate MorphismType = "MUTATE"
	MorphismUnlink MorphismType = "UNLINK"
)

type Node struct {
	URN      URN            `json:"urn"`
	Kind     Kind           `json:"kind"`
	Stratum  Stratum        `json:"stratum"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
	Version  int64          `json:"version"`
}

type Wire struct {
	SourceURN  URN            `json:"source_urn"`
	SourcePort Port           `json:"source_port"`
	TargetURN  URN            `json:"target_urn"`
	TargetPort Port           `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
}

type GraphState struct {
	Nodes map[URN]Node    `json:"nodes"`
	Wires map[string]Wire `json:"wires"`
}

type AddPayload struct {
	URN      URN            `json:"urn"`
	Kind     Kind           `json:"kind"`
	Stratum  Stratum        `json:"stratum,omitempty"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

type LinkPayload struct {
	SourceURN  URN            `json:"source_urn"`
	SourcePort Port           `json:"source_port"`
	TargetURN  URN            `json:"target_urn"`
	TargetPort Port           `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
}

type MutatePayload struct {
	URN             URN            `json:"urn"`
	ExpectedVersion int64          `json:"expected_version"`
	Payload         map[string]any `json:"payload,omitempty"`
	Metadata        map[string]any `json:"metadata,omitempty"`
}

type UnlinkPayload struct {
	SourceURN  URN  `json:"source_urn"`
	SourcePort Port `json:"source_port"`
	TargetURN  URN  `json:"target_urn"`
	TargetPort Port `json:"target_port"`
}

type Envelope struct {
	Type   MorphismType   `json:"type"`
	Actor  URN            `json:"actor"`
	Scope  URN            `json:"scope,omitempty"`
	Add    *AddPayload    `json:"add,omitempty"`
	Link   *LinkPayload   `json:"link,omitempty"`
	Mutate *MutatePayload `json:"mutate,omitempty"`
	Unlink *UnlinkPayload `json:"unlink,omitempty"`
}

type PersistedEnvelope struct {
	Envelope Envelope  `json:"envelope"`
	IssuedAt time.Time `json:"issued_at"`
}

type Program struct {
	Actor     URN        `json:"actor,omitempty"`
	Scope     URN        `json:"scope,omitempty"`
	Envelopes []Envelope `json:"envelopes"`
}

type EvalResult struct {
	State     GraphState        `json:"state"`
	Node      *Node             `json:"node,omitempty"`
	Wire      *Wire             `json:"wire,omitempty"`
	Persisted PersistedEnvelope `json:"persisted"`
	Summary   string            `json:"summary"`
}

type ProgramResult struct {
	State     GraphState          `json:"state"`
	Results   []EvalResult        `json:"results"`
	Persisted []PersistedEnvelope `json:"persisted"`
	Summary   string              `json:"summary"`
}

func NewGraphState() GraphState {
	return GraphState{
		Nodes: map[URN]Node{},
		Wires: map[string]Wire{},
	}
}

func (state GraphState) Clone() GraphState {
	clone := NewGraphState()
	for urn, node := range state.Nodes {
		clone.Nodes[urn] = Node{
			URN:      node.URN,
			Kind:     node.Kind,
			Stratum:  node.Stratum,
			Payload:  cloneMap(node.Payload),
			Metadata: cloneMap(node.Metadata),
			Version:  node.Version,
		}
	}
	for key, wire := range state.Wires {
		clone.Wires[key] = Wire{
			SourceURN:  wire.SourceURN,
			SourcePort: wire.SourcePort,
			TargetURN:  wire.TargetURN,
			TargetPort: wire.TargetPort,
			Config:     cloneMap(wire.Config),
		}
	}
	return clone
}

func cloneMap(input map[string]any) map[string]any {
	if len(input) == 0 {
		return nil
	}
	clone := make(map[string]any, len(input))
	for key, value := range input {
		clone[key] = cloneValue(value)
	}
	return clone
}

func cloneValue(value any) any {
	switch typed := value.(type) {
	case map[string]any:
		return cloneMap(typed)
	case []any:
		clone := make([]any, len(typed))
		for index, item := range typed {
			clone[index] = cloneValue(item)
		}
		return clone
	default:
		return typed
	}
}

func NormalizeStratum(stratum Stratum) Stratum {
	if stratum == "" {
		return StratumMaterialized
	}
	return stratum
}

func WireKey(sourceURN URN, sourcePort Port, targetURN URN, targetPort Port) string {
	return string(sourceURN) + "|" + string(sourcePort) + "|" + string(targetURN) + "|" + string(targetPort)
}
