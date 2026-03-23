package functor

import (
	"strings"
	"testing"
	"time"

	"moos/platform/kernel/internal/cat"
)

func TestCalendarName(t *testing.T) {
	c := Calendar{}
	if got := c.Name(); got != "FUN06_calendar" {
		t.Errorf("Name() = %q, want FUN06_calendar", got)
	}
}

func TestCalendarProject(t *testing.T) {
	now := time.Date(2026, 3, 23, 0, 0, 0, 0, time.UTC)

	state := cat.NewGraphState()
	state.Nodes["urn:prg:1"] = cat.Node{
		URN:       "urn:prg:1",
		TypeID:    "prg_task",
		CreatedAt: now,
		UpdatedAt: now.Add(2 * time.Hour),
		Payload: map[string]any{
			"title":  "Task 034",
			"status": "in_progress",
		},
	}
	state.Nodes["urn:session:1"] = cat.Node{
		URN:       "urn:session:1",
		TypeID:    "agent_session",
		CreatedAt: now,
		Payload: map[string]any{
			"summary":    "Morning session",
			"agent":      "urn:moos:agent:antigraviti",
			"started_at": "2026-03-23T00:10:00Z",
			"status":     "active",
		},
	}
	state.Nodes["urn:cal:1"] = cat.Node{
		URN:    "urn:cal:1",
		TypeID: "calendar_event",
		Payload: map[string]any{
			"summary":    "Studio Shoot",
			"start_time": "2026-03-24T09:00:00Z",
			"end_time":   "2026-03-24T10:00:00Z",
			"status":     "confirmed",
		},
	}

	c := Calendar{}
	res, err := c.Project(state)
	if err != nil {
		t.Fatalf("Project() error: %v", err)
	}
	proj := res.(CalendarProjection)

	if proj.GeneratedAt == "" {
		t.Fatal("GeneratedAt must be set")
	}
	if len(proj.Entries) != 3 {
		t.Fatalf("expected 3 entries, got %d", len(proj.Entries))
	}

	var foundPRG bool
	for _, e := range proj.Entries {
		if e.ID == "urn:prg:1" {
			foundPRG = true
			if e.Status != "confirmed" {
				t.Errorf("prg status=%q, want confirmed", e.Status)
			}
			if e.Color != 5 {
				t.Errorf("prg color=%d, want 5", e.Color)
			}
		}
	}
	if !foundPRG {
		t.Fatal("prg entry not found")
	}
}

func TestRenderICalendar(t *testing.T) {
	proj := CalendarProjection{
		GeneratedAt: "2026-03-23T00:00:00Z",
		Entries: []CalendarEntry{
			{
				ID:      "urn:evt:1",
				Summary: "Demo",
				Start:   "2026-03-24T09:00:00Z",
				End:     "2026-03-24T10:00:00Z",
				Status:  "confirmed",
				Kind:    "calendar_event",
			},
		},
	}

	ics := RenderICalendar(proj, "moos-test")
	for _, token := range []string{"BEGIN:VCALENDAR", "BEGIN:VEVENT", "SUMMARY:Demo", "END:VCALENDAR"} {
		if !strings.Contains(ics, token) {
			t.Fatalf("ics missing %q:\n%s", token, ics)
		}
	}
}
