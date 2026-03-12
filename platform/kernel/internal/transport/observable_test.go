package transport_test

import (
	"bufio"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"moos/platform/kernel/internal/cat"
)

// TestLogFiltering verifies the ?type and ?limit query parameters on GET /log.
func TestLogFiltering(t *testing.T) {
	srv := newTestServer(t)

	// Apply 2 ADD envelopes and 1 LINK between them.
	applyADD := func(urn cat.URN) {
		env := cat.Envelope{
			Type:  cat.ADD,
			Actor: testActor,
			Add:   &cat.AddPayload{URN: urn, TypeID: "node_container"},
		}
		w := doRequest(t, srv.Handler(), "POST", "/morphisms", env)
		if w.Code != http.StatusOK {
			t.Fatalf("ADD %s: got %d — %s", urn, w.Code, w.Body.String())
		}
	}
	applyADD("urn:moos:log-filter:a")
	applyADD("urn:moos:log-filter:b")

	linkEnv := cat.Envelope{
		Type:  cat.LINK,
		Actor: testActor,
		Link: &cat.LinkPayload{
			SourceURN:  "urn:moos:log-filter:a",
			SourcePort: "LINK_NODES",
			TargetURN:  "urn:moos:log-filter:b",
			TargetPort: "LINK_NODES",
		},
	}
	w := doRequest(t, srv.Handler(), "POST", "/morphisms", linkEnv)
	if w.Code != http.StatusOK {
		t.Fatalf("LINK: got %d — %s", w.Code, w.Body.String())
	}

	// ?type=ADD should return exactly 2 entries.
	wType := doRequest(t, srv.Handler(), "GET", "/log?type=ADD", nil)
	if wType.Code != http.StatusOK {
		t.Fatalf("GET /log?type=ADD: got %d", wType.Code)
	}
	var addEntries []cat.PersistedEnvelope
	if err := json.Unmarshal(wType.Body.Bytes(), &addEntries); err != nil {
		t.Fatalf("decode ADD log: %v", err)
	}
	if len(addEntries) != 2 {
		t.Errorf("expected 2 ADD entries, got %d", len(addEntries))
	}

	// ?limit=1 should return exactly 1 entry (the most recent).
	wLimit := doRequest(t, srv.Handler(), "GET", "/log?limit=1", nil)
	if wLimit.Code != http.StatusOK {
		t.Fatalf("GET /log?limit=1: got %d", wLimit.Code)
	}
	var limitEntries []cat.PersistedEnvelope
	if err := json.Unmarshal(wLimit.Body.Bytes(), &limitEntries); err != nil {
		t.Fatalf("decode limit log: %v", err)
	}
	if len(limitEntries) != 1 {
		t.Errorf("expected 1 entry with ?limit=1, got %d", len(limitEntries))
	}
}

// TestLogStreamSSE verifies that GET /log/stream emits SSE events when a morphism is applied.
func TestLogStreamSSE(t *testing.T) {
	srv := newTestServer(t)

	// Start an httptest.Server so we get a real HTTP connection (SSE requires streaming).
	ts := httptest.NewServer(srv.Handler())
	defer ts.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, "GET", ts.URL+"/log/stream", nil)
	if err != nil {
		t.Fatalf("NewRequest: %v", err)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("GET /log/stream: %v", err)
	}
	defer resp.Body.Close()

	if ct := resp.Header.Get("Content-Type"); !strings.HasPrefix(ct, "text/event-stream") {
		t.Errorf("expected Content-Type text/event-stream, got %q", ct)
	}

	// Apply a morphism in the background so the stream receives an event.
	go func() {
		time.Sleep(50 * time.Millisecond)
		env := cat.Envelope{
			Type:  cat.ADD,
			Actor: testActor,
			Add:   &cat.AddPayload{URN: "urn:moos:sse-test:node", TypeID: "node_container"},
		}
		doRequest(t, srv.Handler(), "POST", "/morphisms", env)
	}()

	// Read lines from the SSE stream until we see "event: morphism" or context expires.
	scanner := bufio.NewScanner(resp.Body)
	found := false
	for scanner.Scan() {
		line := scanner.Text()
		if line == "event: morphism" {
			found = true
			break
		}
	}
	if !found {
		if ctx.Err() != nil {
			t.Fatal("timed out waiting for 'event: morphism' line in SSE stream")
		}
		t.Fatal("SSE stream closed without 'event: morphism' line")
	}
}
