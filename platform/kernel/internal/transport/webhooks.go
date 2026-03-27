package transport

import (
	"encoding/json"
	"net/http"
	"regexp"
	"strings"
	"time"

	"moos/platform/kernel/internal/cat"
	"moos/platform/kernel/internal/shell"
)

var prgTagRE = regexp.MustCompile(`\bPRG(\d{3})\b`)

// CalendarEntry is the normalized callback payload for calendar sync ingestion.
type CalendarEntry struct {
	ID          string `json:"id"`
	Summary     string `json:"summary"`
	StartTime   string `json:"start_time"`
	EndTime     string `json:"end_time"`
	Description string `json:"description"`
	SourceType  string `json:"source_type"`
}

// IngestCalendarEvent is a pure mapper from callback payload to morphism envelopes.
// If description contains PRG###, emits ADD(calendar_event) and LINK to the PRG node.
// Otherwise emits ADD(keep_note) at S0.
func IngestCalendarEvent(event CalendarEntry) []cat.Envelope {
	actor := cat.URN("urn:moos:agent:calendar-sync")
	id := strings.TrimSpace(event.ID)
	if id == "" {
		id = time.Now().UTC().Format("20060102150405")
	}
	id = strings.NewReplacer(" ", "-", "/", "-", "\\", "-").Replace(id)

	if m := prgTagRE.FindStringSubmatch(strings.ToUpper(event.Description)); len(m) == 2 {
		prgID := m[1]
		eventURN := cat.URN("urn:moos:calendar_event:" + id)
		prgURN := cat.URN("urn:moos:prg:" + prgID)
		return []cat.Envelope{
			{
				Type:  cat.ADD,
				Actor: actor,
				Add: &cat.AddPayload{
					URN:     eventURN,
					TypeID:  "calendar_event",
					Stratum: cat.S2,
					Payload: map[string]any{
						"id":          event.ID,
						"summary":     event.Summary,
						"start_time":  event.StartTime,
						"end_time":    event.EndTime,
						"description": event.Description,
						"source_type": event.SourceType,
						"prg":         "PRG" + prgID,
					},
				},
			},
			{
				Type:  cat.LINK,
				Actor: actor,
				Link: &cat.LinkPayload{
					SourceURN:  eventURN,
					SourcePort: "out",
					TargetURN:  prgURN,
					TargetPort: "in",
				},
			},
		}
	}

	noteURN := cat.URN("urn:moos:keep_note:" + id)
	return []cat.Envelope{
		{
			Type:  cat.ADD,
			Actor: actor,
			Add: &cat.AddPayload{
				URN:     noteURN,
				TypeID:  "keep_note",
				Stratum: cat.S0,
				Payload: map[string]any{
					"title":       event.Summary,
					"text":        event.Description,
					"start_time":  event.StartTime,
					"end_time":    event.EndTime,
					"source_type": event.SourceType,
					"calendar_id": event.ID,
				},
			},
		},
	}
}

// HandleGCalWebhook processes incoming Google Calendar events and injects them into the hyperspace as SOT.
func HandleGCalWebhook(run shell.RunSubstrate) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var payload map[string]interface{}
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			http.Error(w, "Bad Request", http.StatusBadRequest)
			return
		}

		env := cat.Envelope{
			Type:  cat.ADD,
			Actor: "urn:moos:agent:gcal-sync",
			Add: &cat.AddPayload{
				URN:     cat.URN("urn:moos:event:gcal-" + time.Now().Format("20060102150405")),
				TypeID:  "calendar_event",
				Stratum: "S2",
				Payload: payload,
			},
		}

		if _, err := run.Apply(env); err != nil {
			http.Error(w, "State Application Failed", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusAccepted)
	}
}
