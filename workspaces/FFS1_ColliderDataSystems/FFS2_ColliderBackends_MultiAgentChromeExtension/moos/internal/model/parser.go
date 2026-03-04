package model

import (
	"encoding/json"
	"strings"

	"github.com/collider/moos/internal/morphism"
)

func ParseMorphismEnvelopes(text string) ([]morphism.Envelope, error) {
	blocks := extractJSONBlocks(text)
	if len(blocks) == 0 {
		return nil, nil
	}

	result := make([]morphism.Envelope, 0)
	for _, block := range blocks {
		var single morphism.Envelope
		if err := json.Unmarshal([]byte(block), &single); err == nil && single.Type != "" {
			result = append(result, single)
			continue
		}

		var multiple []morphism.Envelope
		if err := json.Unmarshal([]byte(block), &multiple); err == nil {
			for _, envelope := range multiple {
				if envelope.Type != "" {
					result = append(result, envelope)
				}
			}
		}
	}
	if len(result) == 0 {
		return nil, nil
	}
	return result, nil
}

func extractJSONBlocks(text string) []string {
	lines := strings.Split(text, "\n")
	blocks := make([]string, 0)
	collecting := false
	buffer := make([]string, 0)

	for _, rawLine := range lines {
		line := strings.TrimSpace(rawLine)
		if strings.HasPrefix(line, "```") {
			if !collecting && (line == "```json" || line == "```morphism" || line == "```") {
				collecting = true
				buffer = buffer[:0]
				continue
			}
			if collecting {
				collecting = false
				if len(buffer) > 0 {
					blocks = append(blocks, strings.Join(buffer, "\n"))
				}
				buffer = buffer[:0]
			}
			continue
		}
		if collecting {
			buffer = append(buffer, rawLine)
		}
	}
	return blocks
}
