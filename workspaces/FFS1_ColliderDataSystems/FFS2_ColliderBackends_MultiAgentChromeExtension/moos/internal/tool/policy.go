package tool

import (
	"fmt"
	"strings"
)

type Policy struct {
	MaxInputBytes  int
	MaxExecutionMs int
	BlockedPrefix  []string
}

func DefaultPolicy() Policy {
	return Policy{MaxInputBytes: 16 * 1024, MaxExecutionMs: 5000, BlockedPrefix: []string{"internal_", "system_"}}
}

func (policy Policy) Validate(name string, rawInput []byte) error {
	if strings.TrimSpace(name) == "" {
		return fmt.Errorf("tool name is required")
	}
	if len(rawInput) > policy.MaxInputBytes {
		return fmt.Errorf("input exceeds max bytes")
	}
	for _, prefix := range policy.BlockedPrefix {
		if strings.HasPrefix(name, prefix) {
			return fmt.Errorf("tool blocked by policy")
		}
	}
	return nil
}
