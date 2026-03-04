package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/morphism"
	"github.com/collider/moos/internal/session"
	"github.com/gorilla/websocket"
)

type webSocketGateway struct {
	executor    *morphism.Executor
	sessions    *session.Manager
	bearerToken string
	logger      *slog.Logger
	upgrader    websocket.Upgrader

	mu      sync.RWMutex
	clients map[*webSocketClient]struct{}

	surfaceMu sync.RWMutex
	surfaces  map[string]surfaceRegistration
}

type webSocketClient struct {
	conn *websocket.Conn
	send chan []byte
}

type jsonRPCMessage struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id,omitempty"`
	Method  string          `json:"method,omitempty"`
	Params  json.RawMessage `json:"params,omitempty"`
}

type jsonRPCError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type morphismSubmitParams struct {
	Envelope morphism.Envelope `json:"envelope"`
}

type sessionSendParams struct {
	SessionID string `json:"session_id"`
	Text      string `json:"text"`
}

type sessionCloseParams struct {
	SessionID string `json:"session_id"`
}

type surfaceRegisterParams struct {
	SurfaceID string `json:"surface_id"`
	URN       string `json:"urn"`
	Kind      string `json:"kind"`
	Name      string `json:"name"`
}

type surfaceRegistration struct {
	SurfaceID  string `json:"surface_id"`
	URN        string `json:"urn"`
	Kind       string `json:"kind"`
	Name       string `json:"name"`
	Registered string `json:"registered_at"`
}

func newWebSocketGateway(executor *morphism.Executor, sessions *session.Manager, bearerToken string, logger *slog.Logger) http.Handler {
	if logger == nil {
		logger = slog.Default()
	}
	gateway := &webSocketGateway{
		executor:    executor,
		sessions:    sessions,
		bearerToken: bearerToken,
		logger:      logger,
		upgrader: websocket.Upgrader{
			CheckOrigin: func(request *http.Request) bool {
				return true
			},
		},
		clients:  map[*webSocketClient]struct{}{},
		surfaces: map[string]surfaceRegistration{},
	}
	if sessions != nil {
		sessions.SetBroadcaster(func(_ string, event session.Event) {
			gateway.broadcastSessionEvent(event)
		})
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", gateway.handle)
	return mux
}

func (gateway *webSocketGateway) handle(writer http.ResponseWriter, request *http.Request) {
	if !authorizeAPIRequest(writer, request, gateway.bearerToken) {
		return
	}
	connection, err := gateway.upgrader.Upgrade(writer, request, nil)
	if err != nil {
		gateway.logger.Warn("websocket upgrade failed", "error", err)
		return
	}

	client := &webSocketClient{conn: connection, send: make(chan []byte, 32)}
	gateway.register(client)
	defer gateway.unregister(client)

	go client.writeLoop(gateway.logger)
	client.readLoop(gateway)
}

func (gateway *webSocketGateway) register(client *webSocketClient) {
	gateway.mu.Lock()
	defer gateway.mu.Unlock()
	gateway.clients[client] = struct{}{}
}

func (gateway *webSocketGateway) unregister(client *webSocketClient) {
	gateway.mu.Lock()
	defer gateway.mu.Unlock()
	if _, exists := gateway.clients[client]; !exists {
		return
	}
	delete(gateway.clients, client)
	close(client.send)
	_ = client.conn.Close()
}

func (gateway *webSocketGateway) broadcast(payload []byte) {
	gateway.mu.RLock()
	defer gateway.mu.RUnlock()
	for client := range gateway.clients {
		select {
		case client.send <- payload:
		default:
		}
	}
}

func (client *webSocketClient) writeLoop(logger *slog.Logger) {
	for message := range client.send {
		if err := client.conn.WriteMessage(websocket.TextMessage, message); err != nil {
			logger.Warn("websocket write failed", "error", err)
			return
		}
	}
}

func (client *webSocketClient) readLoop(gateway *webSocketGateway) {
	for {
		messageType, payload, err := client.conn.ReadMessage()
		if err != nil {
			return
		}
		if messageType != websocket.TextMessage {
			continue
		}
		gateway.processMessage(client, payload)
	}
}

func (gateway *webSocketGateway) processMessage(client *webSocketClient, payload []byte) {
	var message jsonRPCMessage
	if err := json.Unmarshal(payload, &message); err != nil {
		gateway.sendError(client, nil, -32700, "invalid json payload")
		return
	}
	switch message.Method {
	case "morphism.submit":
		gateway.handleMorphismSubmit(client, message)
	case "session.create":
		gateway.handleSessionCreate(client, message)
	case "session.send":
		gateway.handleSessionSend(client, message)
	case "session.list":
		gateway.handleSessionList(client, message)
	case "session.close":
		gateway.handleSessionClose(client, message)
	case "surface.register":
		gateway.handleSurfaceRegister(client, message)
	case "surface.list":
		gateway.handleSurfaceList(client, message)
	default:
		gateway.sendError(client, message.ID, -32601, "method not found")
	}
}

func (gateway *webSocketGateway) handleMorphismSubmit(client *webSocketClient, message jsonRPCMessage) {
	if gateway.executor == nil {
		gateway.sendError(client, message.ID, -32000, "database not configured")
		return
	}

	var envelope morphism.Envelope
	if err := decodeEnvelope(message.Params, &envelope); err != nil {
		gateway.sendError(client, message.ID, -32602, "invalid morphism envelope")
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	nextVersion, err := gateway.executor.Apply(ctx, envelope)
	if err != nil {
		gateway.sendApplyError(client, message.ID, nextVersion, err)
		return
	}

	gateway.sendResult(client, message.ID, map[string]any{"accepted": true, "next_version": nextVersion})
	gateway.broadcastMorphism(envelope)
}

func (gateway *webSocketGateway) handleSessionCreate(client *webSocketClient, message jsonRPCMessage) {
	if gateway.sessions == nil {
		gateway.sendError(client, message.ID, -32000, "sessions not configured")
		return
	}
	summary, err := gateway.sessions.Create()
	if err != nil {
		gateway.sendError(client, message.ID, -32000, err.Error())
		return
	}
	gateway.sendResult(client, message.ID, map[string]any{
		"session_id": summary.SessionID,
		"root_urn":   summary.RootURN,
	})
}

func (gateway *webSocketGateway) handleSessionSend(client *webSocketClient, message jsonRPCMessage) {
	if gateway.sessions == nil {
		gateway.sendError(client, message.ID, -32000, "sessions not configured")
		return
	}
	var payload sessionSendParams
	if err := json.Unmarshal(message.Params, &payload); err != nil {
		gateway.sendError(client, message.ID, -32602, "invalid session.send params")
		return
	}
	payload.SessionID = strings.TrimSpace(payload.SessionID)
	if payload.SessionID == "" || strings.TrimSpace(payload.Text) == "" {
		gateway.sendError(client, message.ID, -32602, "session_id and text are required")
		return
	}
	if err := gateway.sessions.Send(payload.SessionID, payload.Text); err != nil {
		gateway.sendError(client, message.ID, -32004, err.Error())
		return
	}
	gateway.sendResult(client, message.ID, map[string]any{"accepted": true})
}

func (gateway *webSocketGateway) handleSessionList(client *webSocketClient, message jsonRPCMessage) {
	if gateway.sessions == nil {
		gateway.sendError(client, message.ID, -32000, "sessions not configured")
		return
	}
	gateway.sendResult(client, message.ID, gateway.sessions.List())
}

func (gateway *webSocketGateway) handleSessionClose(client *webSocketClient, message jsonRPCMessage) {
	if gateway.sessions == nil {
		gateway.sendError(client, message.ID, -32000, "sessions not configured")
		return
	}
	var payload sessionCloseParams
	if err := json.Unmarshal(message.Params, &payload); err != nil {
		gateway.sendError(client, message.ID, -32602, "invalid session.close params")
		return
	}
	payload.SessionID = strings.TrimSpace(payload.SessionID)
	if payload.SessionID == "" {
		gateway.sendError(client, message.ID, -32602, "session_id is required")
		return
	}
	if err := gateway.sessions.Close(payload.SessionID); err != nil {
		gateway.sendError(client, message.ID, -32004, err.Error())
		return
	}
	gateway.sendResult(client, message.ID, map[string]any{"closed": true})
}

func (gateway *webSocketGateway) handleSurfaceRegister(client *webSocketClient, message jsonRPCMessage) {
	var payload surfaceRegisterParams
	if err := json.Unmarshal(message.Params, &payload); err != nil {
		gateway.sendError(client, message.ID, -32602, "invalid surface.register params")
		return
	}
	payload.SurfaceID = strings.TrimSpace(payload.SurfaceID)
	payload.URN = strings.TrimSpace(payload.URN)
	payload.Kind = strings.TrimSpace(payload.Kind)
	payload.Name = strings.TrimSpace(payload.Name)

	if payload.SurfaceID == "" {
		gateway.sendError(client, message.ID, -32602, "surface_id is required")
		return
	}
	if payload.URN == "" {
		payload.URN = "urn:moos:surface:" + payload.SurfaceID
	}
	if payload.Kind == "" {
		payload.Kind = "surface"
	}
	if payload.Name == "" {
		payload.Name = payload.SurfaceID
	}

	if gateway.executor != nil {
		record := container.Record{
			URN:             payload.URN,
			Kind:            payload.Kind,
			InterfaceJSON:   json.RawMessage(`{"inputs":[],"outputs":[]}`),
			KernelJSON:      mustMarshalJSON(map[string]any{"name": payload.Name, "surface_id": payload.SurfaceID, "registered": true}),
			PermissionsJSON: json.RawMessage(`{"visibility":"workspace"}`),
			Version:         1,
		}
		if err := gateway.executor.Add(context.Background(), record); err != nil && !errors.Is(err, container.ErrAlreadyExists) {
			gateway.sendError(client, message.ID, -32000, "failed to register surface")
			return
		}
	}

	entry := surfaceRegistration{
		SurfaceID:  payload.SurfaceID,
		URN:        payload.URN,
		Kind:       payload.Kind,
		Name:       payload.Name,
		Registered: time.Now().UTC().Format(time.RFC3339),
	}

	gateway.surfaceMu.Lock()
	gateway.surfaces[payload.SurfaceID] = entry
	gateway.surfaceMu.Unlock()

	gateway.sendResult(client, message.ID, entry)
	gateway.broadcastSurfaceSync("surface.registered", entry)
}

func (gateway *webSocketGateway) handleSurfaceList(client *webSocketClient, message jsonRPCMessage) {
	gateway.surfaceMu.RLock()
	list := make([]surfaceRegistration, 0, len(gateway.surfaces))
	for _, entry := range gateway.surfaces {
		list = append(list, entry)
	}
	gateway.surfaceMu.RUnlock()
	gateway.sendResult(client, message.ID, list)
}

func decodeEnvelope(params json.RawMessage, envelope *morphism.Envelope) error {
	if len(params) == 0 {
		return morphism.ErrInvalidEnvelope
	}
	var wrapped morphismSubmitParams
	if err := json.Unmarshal(params, &wrapped); err == nil && wrapped.Envelope.Type != "" {
		*envelope = wrapped.Envelope
		return nil
	}
	if err := json.Unmarshal(params, envelope); err != nil {
		return err
	}
	if envelope.Type == "" {
		return morphism.ErrInvalidEnvelope
	}
	return nil
}

func (gateway *webSocketGateway) sendApplyError(client *webSocketClient, id json.RawMessage, nextVersion int64, err error) {
	switch {
	case errors.Is(err, morphism.ErrInvalidEnvelope):
		gateway.sendError(client, id, -32602, "invalid morphism envelope")
	case errors.Is(err, container.ErrNotFound):
		gateway.sendError(client, id, -32004, "container not found")
	case errors.Is(err, container.ErrAlreadyExists):
		gateway.sendError(client, id, -32009, "resource already exists")
	case errors.Is(err, container.ErrVersionConflict):
		gateway.sendError(client, id, -32010, "version conflict: current version "+strconv.FormatInt(nextVersion, 10))
	default:
		gateway.sendError(client, id, -32000, "failed to apply morphism")
	}
}

func (gateway *webSocketGateway) broadcastSessionEvent(event session.Event) {
	notification := map[string]any{
		"jsonrpc": "2.0",
		"method":  event.Method,
		"params":  event.Params,
	}
	encoded, err := json.Marshal(notification)
	if err != nil {
		gateway.logger.Warn("failed to encode session event", "error", err)
		return
	}
	gateway.broadcast(encoded)
}

func (gateway *webSocketGateway) sendResult(client *webSocketClient, id json.RawMessage, result any) {
	if len(id) == 0 {
		id = json.RawMessage("null")
	}
	response := map[string]any{
		"jsonrpc": "2.0",
		"id":      id,
		"result":  result,
	}
	encoded, err := json.Marshal(response)
	if err != nil {
		return
	}
	select {
	case client.send <- encoded:
	default:
	}
}

func (gateway *webSocketGateway) sendError(client *webSocketClient, id json.RawMessage, code int, message string) {
	if len(id) == 0 {
		id = json.RawMessage("null")
	}
	response := map[string]any{
		"jsonrpc": "2.0",
		"id":      id,
		"error": jsonRPCError{
			Code:    code,
			Message: message,
		},
	}
	encoded, err := json.Marshal(response)
	if err != nil {
		return
	}
	select {
	case client.send <- encoded:
	default:
	}
}

func (gateway *webSocketGateway) broadcastMorphism(envelope morphism.Envelope) {
	notification := map[string]any{
		"jsonrpc": "2.0",
		"method":  "stream.morphism",
		"params": map[string]any{
			"envelope": envelope,
		},
	}
	encoded, err := json.Marshal(notification)
	if err != nil {
		gateway.logger.Warn("failed to encode morphism notification", "error", fmt.Errorf("%w", err))
		return
	}
	gateway.broadcast(encoded)
	gateway.broadcastSurfaceSync("sync.active_state_delta", map[string]any{"envelope": envelope})
}

func (gateway *webSocketGateway) broadcastActiveState(nodes any, edges any) {
	gateway.broadcastSurfaceSync("sync.active_state", map[string]any{
		"nodes": nodes,
		"edges": edges,
	})
}

func (gateway *webSocketGateway) broadcastSurfaceSync(method string, params any) {
	notification := map[string]any{
		"jsonrpc": "2.0",
		"method":  method,
		"params":  params,
	}
	encoded, err := json.Marshal(notification)
	if err != nil {
		gateway.logger.Warn("failed to encode surface sync event", "error", err)
		return
	}
	gateway.broadcast(encoded)
}

func mustMarshalJSON(value any) json.RawMessage {
	encoded, err := json.Marshal(value)
	if err != nil {
		return json.RawMessage(`{}`)
	}
	return encoded
}
