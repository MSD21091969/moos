package cat

// AddPayload is the data for the ADD natural transformation: ∅ → Node.
type AddPayload struct {
	URN      URN            `json:"urn"`
	TypeID   TypeID         `json:"type_id"`
	Stratum  Stratum        `json:"stratum,omitempty"`
	Payload  map[string]any `json:"payload,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`
}

// LinkPayload is the data for the LINK natural transformation: N × N → Wire.
// The 4-tuple must be unique.
type LinkPayload struct {
	SourceURN  URN            `json:"source_urn"`
	SourcePort Port           `json:"source_port"`
	TargetURN  URN            `json:"target_urn"`
	TargetPort Port           `json:"target_port"`
	Config     map[string]any `json:"config,omitempty"`
}

// MutatePayload is the data for the MUTATE natural transformation: N → N.
// Updates a Node's payload under version-CAS (optimistic concurrency).
type MutatePayload struct {
	URN             URN            `json:"urn"`
	ExpectedVersion int64          `json:"expected_version"`
	Payload         map[string]any `json:"payload,omitempty"`
	Metadata        map[string]any `json:"metadata,omitempty"`
}

// UnlinkPayload is the data for the UNLINK natural transformation: Wire → ∅.
// Removes a wire by its 4-tuple key.
type UnlinkPayload struct {
	SourceURN  URN  `json:"source_urn"`
	SourcePort Port `json:"source_port"`
	TargetURN  URN  `json:"target_urn"`
	TargetPort Port `json:"target_port"`
}
