package functor

import (
	"fmt"
	"sort"
	"strings"
	"time"

	"moos/platform/kernel/internal/cat"
)

// Calendar implements Projector for FUN06: F_cal: C -> GCal.
type Calendar struct{}

// Name returns the functor identifier.
func (c Calendar) Name() string { return "FUN06_calendar" }

// Project maps graph state to calendar-shaped entries.
func (c Calendar) Project(state cat.GraphState) (any, error) {
	return c.ProjectCalendar(state), nil
}

// ProjectCalendar is the typed projection for direct callers.
func (c Calendar) ProjectCalendar(state cat.GraphState) CalendarProjection {
	entries := make([]CalendarEntry, 0, len(state.Nodes))

	for _, n := range state.Nodes {
		switch n.TypeID {
		case "prg_task":
			entries = append(entries, projectPRGTask(n))
		case "agent_session":
			entries = append(entries, projectAgentSession(n))
		case "calendar_event":
			entries = append(entries, projectCalendarEvent(n))
		}
	}

	sort.Slice(entries, func(i, j int) bool {
		it := sortTime(entries[i].Start)
		jt := sortTime(entries[j].Start)
		if !it.Equal(jt) {
			return it.Before(jt)
		}
		return entries[i].ID < entries[j].ID
	})

	return CalendarProjection{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339Nano),
		Entries:     entries,
	}
}

func projectPRGTask(n cat.Node) CalendarEntry {
	statusRaw := strings.ToLower(payloadString(n.Payload, "status"))
	calStatus, color := mapPRGStatus(statusRaw)
	start := normalizeTimeString(payloadString(n.Payload, "started_at"))
	if start == "" {
		start = formatTime(n.CreatedAt)
	}
	end := normalizeTimeString(payloadString(n.Payload, "completed_at"))
	if end == "" {
		end = formatTime(n.UpdatedAt)
	}

	summary := firstNonEmpty(
		payloadString(n.Payload, "title"),
		payloadString(n.Payload, "label"),
		payloadString(n.Payload, "name"),
		string(n.URN),
	)

	return CalendarEntry{
		ID:          string(n.URN),
		Summary:     summary,
		Description: payloadString(n.Payload, "description"),
		Start:       start,
		End:         end,
		Status:      calStatus,
		Color:       color,
		Source:      string(n.URN),
		Kind:        "prg_task",
	}
}

func projectAgentSession(n cat.Node) CalendarEntry {
	started := normalizeTimeString(payloadString(n.Payload, "started_at"))
	if started == "" {
		started = formatTime(n.CreatedAt)
	}
	ended := formatTime(n.UpdatedAt)

	status := "tentative"
	if strings.EqualFold(payloadString(n.Payload, "status"), "active") {
		status = "confirmed"
	}

	summary := firstNonEmpty(
		payloadString(n.Payload, "summary"),
		"Agent session",
	)
	agent := payloadString(n.Payload, "agent")
	desc := summary
	if agent != "" {
		desc = fmt.Sprintf("%s (%s)", summary, agent)
	}

	return CalendarEntry{
		ID:          string(n.URN),
		Summary:     "Session: " + summary,
		Description: desc,
		Start:       started,
		End:         ended,
		Status:      status,
		Color:       1,
		Source:      string(n.URN),
		Kind:        "agent_session",
	}
}

func projectCalendarEvent(n cat.Node) CalendarEntry {
	start := firstNonEmpty(
		normalizeTimeString(payloadString(n.Payload, "start_time")),
		normalizeTimeString(payloadString(n.Payload, "start")),
		normalizeTimeString(payloadString(n.Payload, "start_at")),
		formatTime(n.CreatedAt),
	)
	end := firstNonEmpty(
		normalizeTimeString(payloadString(n.Payload, "end_time")),
		normalizeTimeString(payloadString(n.Payload, "end")),
		normalizeTimeString(payloadString(n.Payload, "end_at")),
		formatTime(n.UpdatedAt),
	)
	summary := firstNonEmpty(
		payloadString(n.Payload, "summary"),
		payloadString(n.Payload, "title"),
		payloadString(n.Payload, "name"),
		payloadString(n.Payload, "label"),
		string(n.URN),
	)
	status := firstNonEmpty(strings.ToLower(payloadString(n.Payload, "status")), "confirmed")

	return CalendarEntry{
		ID:          string(n.URN),
		Summary:     summary,
		Description: payloadString(n.Payload, "description"),
		Start:       start,
		End:         end,
		Status:      status,
		Color:       2,
		Source:      string(n.URN),
		Kind:        "calendar_event",
	}
}

func mapPRGStatus(status string) (string, int) {
	switch status {
	case "done", "completed":
		return "confirmed", 10
	case "in_progress", "active":
		return "confirmed", 5
	case "blocked", "failed":
		return "tentative", 11
	default:
		return "tentative", 9
	}
}

func payloadString(payload map[string]any, key string) string {
	if payload == nil {
		return ""
	}
	v, ok := payload[key]
	if !ok || v == nil {
		return ""
	}
	s, ok := v.(string)
	if !ok {
		return ""
	}
	return strings.TrimSpace(s)
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if strings.TrimSpace(v) != "" {
			return strings.TrimSpace(v)
		}
	}
	return ""
}

func normalizeTimeString(s string) string {
	s = strings.TrimSpace(s)
	if s == "" {
		return ""
	}
	layouts := []string{
		time.RFC3339Nano,
		time.RFC3339,
		"2006-01-02 15:04:05Z07:00",
		"2006-01-02 15:04:05",
		"2006-01-02",
	}
	for _, layout := range layouts {
		if t, err := time.Parse(layout, s); err == nil {
			return t.UTC().Format(time.RFC3339Nano)
		}
	}
	return s
}

func sortTime(v string) time.Time {
	if strings.TrimSpace(v) == "" {
		return time.Date(9999, 1, 1, 0, 0, 0, 0, time.UTC)
	}
	if t, err := time.Parse(time.RFC3339Nano, v); err == nil {
		return t
	}
	if t, err := time.Parse(time.RFC3339, v); err == nil {
		return t
	}
	return time.Date(9999, 1, 1, 0, 0, 0, 0, time.UTC)
}

// RenderICalendar converts the calendar projection to RFC 5545-ish text.
func RenderICalendar(proj CalendarProjection, calName string) string {
	if strings.TrimSpace(calName) == "" {
		calName = "moos-calendar"
	}
	var b strings.Builder
	b.WriteString("BEGIN:VCALENDAR\r\n")
	b.WriteString("VERSION:2.0\r\n")
	b.WriteString("PRODID:-//moos//FUN06 Calendar//EN\r\n")
	b.WriteString("CALSCALE:GREGORIAN\r\n")
	b.WriteString("X-WR-CALNAME:" + escapeICS(calName) + "\r\n")

	now := time.Now().UTC().Format("20060102T150405Z")
	for _, e := range proj.Entries {
		start := icsTime(e.Start)
		if start == "" {
			continue
		}
		end := icsTime(e.End)
		if end == "" {
			end = start
		}
		uid := e.ID
		if uid == "" {
			uid = e.Source
		}
		if uid == "" {
			uid = fmt.Sprintf("event-%s", now)
		}

		b.WriteString("BEGIN:VEVENT\r\n")
		b.WriteString("UID:" + escapeICS(uid) + "\r\n")
		b.WriteString("DTSTAMP:" + now + "\r\n")
		b.WriteString("DTSTART:" + start + "\r\n")
		b.WriteString("DTEND:" + end + "\r\n")
		b.WriteString("SUMMARY:" + escapeICS(e.Summary) + "\r\n")
		if strings.TrimSpace(e.Description) != "" {
			b.WriteString("DESCRIPTION:" + escapeICS(e.Description) + "\r\n")
		}
		b.WriteString("STATUS:" + strings.ToUpper(firstNonEmpty(e.Status, "CONFIRMED")) + "\r\n")
		b.WriteString("CATEGORIES:" + escapeICS(e.Kind) + "\r\n")
		b.WriteString("END:VEVENT\r\n")
	}

	b.WriteString("END:VCALENDAR\r\n")
	return b.String()
}

func icsTime(s string) string {
	s = strings.TrimSpace(s)
	if s == "" {
		return ""
	}
	layouts := []string{time.RFC3339Nano, time.RFC3339}
	for _, layout := range layouts {
		if t, err := time.Parse(layout, s); err == nil {
			return t.UTC().Format("20060102T150405Z")
		}
	}
	return ""
}

func escapeICS(s string) string {
	s = strings.ReplaceAll(s, "\\", "\\\\")
	s = strings.ReplaceAll(s, ";", "\\;")
	s = strings.ReplaceAll(s, ",", "\\,")
	s = strings.ReplaceAll(s, "\r\n", "\\n")
	s = strings.ReplaceAll(s, "\n", "\\n")
	return s
}
