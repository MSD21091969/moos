package cat

// AddPayload is the data for the ADD natural transformation: ∅ → Container.
// Creates a new Node (URN enters Ob(C)).
type AddPayload struct {
	URN      URN            `json:"urn"`
	Kind     Kind           `json:"kind"`
	Stratum  Stratum        `json:"stratum,omitempty"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// LinkPayload is the data for the LINK natural transformation: C × C → Wire.
// Creates a new Wire (edge enters Hom(C)). The 4-tuple must be unique (AX4).
type LinkPayload struct {
	SourceURN  URN            `json:"source_urn"`
	SourcePort Port           `json:"source_port"`
	TargetURN  URN            `json:"target_urn"`
	TargetPort Port           `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
}

// MutatePayload is the data for the MUTATE natural transformation: C → C.
// Updates a Node's payload under version-CAS (optimistic concurrency).
type MutatePayload struct {
	URN             URN            `json:"urn"`
	ExpectedVersion int64          `json:"expected_version"`
	Payload         map[string]any `json:"payload,omitempty"`
	Metadata        map[string]any `json:"metadata,omitempty"`
}

// UnlinkPayload is the data for the UNLINK natural transformation: Wire → ∅.
// Removes a wire by its 4-tuple key (AX4).
type UnlinkPayload struct {
	SourceURN  URN  `json:"source_urn"`
	SourcePort Port `json:"source_port"`
	TargetURN  URN  `json:"target_urn"`
	TargetPort Port `json:"target_port"`
}
