package main

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/model"
	"github.com/collider/moos/internal/morphism"
	"github.com/collider/moos/internal/session"
	"github.com/gorilla/websocket"
)

func TestWebSocketMorphismSubmitAndBroadcast(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := morphism.NewExecutor(store, "urn:moos:actor:system")
	dispatcher := model.NewDispatcher("anthropic", model.AnthropicAdapter{}, model.GeminiAdapter{})
	sessions := session.NewManager(executor, dispatcher, time.Minute, 50*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer sessions.Shutdown()
	handler := newWebSocketGateway(executor, sessions, "", slog.New(slog.NewTextHandler(io.Discard, nil)))
	server := httptest.NewServer(handler)
	defer server.Close()

	wsURL := "ws" + strings.TrimPrefix(server.URL, "http")
	clientA, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("failed to connect client A: %v", err)
	}
	defer clientA.Close()

	clientB, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("failed to connect client B: %v", err)
	}
	defer clientB.Close()

	_ = clientA.SetReadDeadline(time.Now().Add(5 * time.Second))
	_ = clientB.SetReadDeadline(time.Now().Add(5 * time.Second))

	request := map[string]any{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "morphism.submit",
		"params": map[string]any{
			"envelope": map[string]any{
				"type": "ADD",
				"add": map[string]any{
					"container": map[string]any{
						"URN":  "urn:moos:ws:add:1",
						"Kind": "data",
					},
				},
			},
		},
	}
	if err := clientA.WriteJSON(request); err != nil {
		t.Fatalf("failed to send submit request: %v", err)
	}

	_, rawResponse, err := clientA.ReadMessage()
	if err != nil {
		t.Fatalf("failed to read submit response: %v", err)
	}
	var response map[string]any
	if err := json.Unmarshal(rawResponse, &response); err != nil {
		t.Fatalf("failed to decode submit response: %v", err)
	}
	if _, hasResult := response["result"]; !hasResult {
		t.Fatalf("expected result in response, got %v", response)
	}

	_, rawBroadcast, err := clientB.ReadMessage()
	if err != nil {
		t.Fatalf("failed to read broadcast: %v", err)
	}
	var broadcast map[string]any
	if err := json.Unmarshal(rawBroadcast, &broadcast); err != nil {
		t.Fatalf("failed to decode broadcast: %v", err)
	}
	if broadcast["method"] != "stream.morphism" {
		t.Fatalf("expected stream.morphism notification, got %v", broadcast)
	}

	if _, ok := store.records["urn:moos:ws:add:1"]; !ok {
		t.Fatalf("expected container to be created")
	}
	if len(store.logs) != 1 || store.logs[0].Type != "ADD" {
		t.Fatalf("expected one ADD log entry")
	}
}

func TestWebSocketGatewayAuth(t *testing.T) {
	handler := newWebSocketGateway(nil, nil, "secret-token", slog.New(slog.NewTextHandler(io.Discard, nil)))
	server := httptest.NewServer(handler)
	defer server.Close()

	wsURL := "ws" + strings.TrimPrefix(server.URL, "http")

	_, response, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err == nil {
		t.Fatalf("expected unauthorized websocket handshake")
	}
	if response == nil || response.StatusCode != http.StatusUnauthorized {
		t.Fatalf("expected 401 unauthorized, got %#v", response)
	}

	headers := http.Header{}
	headers.Set("Authorization", "Bearer secret-token")
	client, _, err := websocket.DefaultDialer.Dial(wsURL, headers)
	if err != nil {
		t.Fatalf("expected authorized websocket handshake, got %v", err)
	}
	_ = client.Close()
}

func TestWebSocketSessionCreateAndSend(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := morphism.NewExecutor(store, "urn:moos:actor:system")
	dispatcher := model.NewDispatcher("anthropic", model.AnthropicAdapter{}, model.GeminiAdapter{})
	sessions := session.NewManager(executor, dispatcher, time.Minute, 50*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer sessions.Shutdown()
	handler := newWebSocketGateway(executor, sessions, "", slog.New(slog.NewTextHandler(io.Discard, nil)))
	server := httptest.NewServer(handler)
	defer server.Close()

	wsURL := "ws" + strings.TrimPrefix(server.URL, "http")
	client, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("failed to connect websocket client: %v", err)
	}
	defer client.Close()

	_ = client.SetReadDeadline(time.Now().Add(5 * time.Second))

	createReq := map[string]any{"jsonrpc": "2.0", "id": 1, "method": "session.create", "params": map[string]any{}}
	if err := client.WriteJSON(createReq); err != nil {
		t.Fatalf("failed to send session.create: %v", err)
	}

	_, createRaw, err := client.ReadMessage()
	if err != nil {
		t.Fatalf("failed to read session.create response: %v", err)
	}
	var createResp map[string]any
	if err := json.Unmarshal(createRaw, &createResp); err != nil {
		t.Fatalf("failed to decode create response: %v", err)
	}
	result, ok := createResp["result"].(map[string]any)
	if !ok {
		t.Fatalf("expected result object in create response")
	}
	sessionID, _ := result["session_id"].(string)
	if sessionID == "" {
		t.Fatalf("expected session_id in create response")
	}

	sendReq := map[string]any{
		"jsonrpc": "2.0",
		"id":      2,
		"method":  "session.send",
		"params": map[string]any{
			"session_id": sessionID,
			"text":       "hello from phase2",
		},
	}
	if err := client.WriteJSON(sendReq); err != nil {
		t.Fatalf("failed to send session.send: %v", err)
	}

	seenThinking := false
	seenTextDelta := false
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		_, raw, readErr := client.ReadMessage()
		if readErr != nil {
			t.Fatalf("failed to read websocket event: %v", readErr)
		}
		var message map[string]any
		if err := json.Unmarshal(raw, &message); err != nil {
			continue
		}
		method, _ := message["method"].(string)
		if method == "stream.thinking" {
			seenThinking = true
		}
		if method == "stream.text_delta" {
			seenTextDelta = true
		}
		if seenThinking && seenTextDelta {
			break
		}
	}

	if !seenThinking || !seenTextDelta {
		t.Fatalf("expected stream.thinking and stream.text_delta events")
	}
}

func TestWebSocketSurfaceRegisterAndList(t *testing.T) {
	store := &fakeStore{records: map[string]container.Record{}, wires: map[string]container.WireRecord{}}
	executor := morphism.NewExecutor(store, "urn:moos:actor:system")
	dispatcher := model.NewDispatcher("anthropic", model.AnthropicAdapter{}, model.GeminiAdapter{})
	sessions := session.NewManager(executor, dispatcher, time.Minute, 50*time.Millisecond, slog.New(slog.NewTextHandler(io.Discard, nil)))
	defer sessions.Shutdown()
	handler := newWebSocketGateway(executor, sessions, "", slog.New(slog.NewTextHandler(io.Discard, nil)))
	server := httptest.NewServer(handler)
	defer server.Close()

	wsURL := "ws" + strings.TrimPrefix(server.URL, "http")
	client, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("failed to connect websocket client: %v", err)
	}
	defer client.Close()

	_ = client.SetReadDeadline(time.Now().Add(5 * time.Second))

	registerReq := map[string]any{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "surface.register",
		"params": map[string]any{
			"surface_id": "ffs4",
			"name":       "FFS4 Sidepanel",
		},
	}
	if err := client.WriteJSON(registerReq); err != nil {
		t.Fatalf("failed to send surface.register: %v", err)
	}

	_, registerRaw, err := client.ReadMessage()
	if err != nil {
		t.Fatalf("failed to read surface.register response: %v", err)
	}
	var registerResp map[string]any
	if err := json.Unmarshal(registerRaw, &registerResp); err != nil {
		t.Fatalf("failed to decode register response: %v", err)
	}
	registerResult, _ := registerResp["result"].(map[string]any)
	if registerResult == nil || registerResult["surface_id"] != "ffs4" {
		t.Fatalf("expected surface_id ffs4 in register response")
	}

	listReq := map[string]any{"jsonrpc": "2.0", "id": 2, "method": "surface.list", "params": map[string]any{}}
	if err := client.WriteJSON(listReq); err != nil {
		t.Fatalf("failed to send surface.list: %v", err)
	}

	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		_, raw, readErr := client.ReadMessage()
		if readErr != nil {
			t.Fatalf("failed to read websocket message: %v", readErr)
		}
		var message map[string]any
		if err := json.Unmarshal(raw, &message); err != nil {
			continue
		}
		if message["id"] == nil {
			continue
		}
		resultList, ok := message["result"].([]any)
		if !ok {
			continue
		}
		if len(resultList) == 0 {
			t.Fatalf("expected at least one registered surface")
		}
		first, _ := resultList[0].(map[string]any)
		if first["surface_id"] != "ffs4" {
			t.Fatalf("expected first surface_id ffs4")
		}
		return
	}

	t.Fatalf("did not receive surface.list response")
}
