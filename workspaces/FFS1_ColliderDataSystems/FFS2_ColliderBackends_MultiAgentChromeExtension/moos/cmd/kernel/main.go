package main

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/collider/moos/internal/config"
	"github.com/collider/moos/internal/container"
	"github.com/collider/moos/internal/migrate"
	"github.com/collider/moos/internal/model"
	"github.com/collider/moos/internal/morphism"
	"github.com/collider/moos/internal/session"
	"github.com/collider/moos/internal/tool"
)

type containerStoreAPI interface {
	Health(ctx context.Context) error
	GetByURN(ctx context.Context, urn string) (*container.Record, error)
	Create(ctx context.Context, record container.Record) error
	ListChildren(ctx context.Context, parentURN string) ([]container.Record, error)
	TreeTraversal(ctx context.Context, rootURN string) ([]container.Record, error)
	MutateKernel(ctx context.Context, urn string, expectedVersion int64, kernelJSON json.RawMessage) (int64, error)
	Link(ctx context.Context, wire container.WireRecord) error
	Unlink(ctx context.Context, wire container.WireRecord) error
	AppendMorphismLog(ctx context.Context, record container.MorphismLogRecord) error
	ListMorphismLog(ctx context.Context, query container.MorphismLogQuery) ([]container.MorphismLogEntry, error)
}

type mutateKernelRequest struct {
	ExpectedVersion int64           `json:"expected_version"`
	KernelJSON      json.RawMessage `json:"kernel_json"`
}

type mutateKernelResponse struct {
	URN     string `json:"urn"`
	Version int64  `json:"version"`
}

type wireRequest struct {
	FromPort     string          `json:"from_port"`
	ToURN        string          `json:"to_urn"`
	ToPort       string          `json:"to_port"`
	MetadataJSON json.RawMessage `json:"metadata_json"`
}

func main() {
	cfg := config.Load()
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

	if cfg.MigrationsAutoApply {
		if cfg.DatabaseURL == "" {
			logger.Error("startup migrations enabled but DATABASE_URL is missing")
			os.Exit(1)
		}
		runner, err := migrate.NewRunner(cfg.DatabaseURL, cfg.MigrationsDir)
		if err != nil {
			logger.Error("failed to initialize migration runner", "error", err)
			os.Exit(1)
		}
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
		applied, upErr := runner.Up(ctx)
		cancel()
		_ = runner.Close()
		if upErr != nil {
			logger.Error("startup migrations failed", "error", upErr)
			os.Exit(1)
		}
		logger.Info("startup migrations completed", "applied_count", len(applied), "migrations_dir", cfg.MigrationsDir)
	}

	var containerStore *container.Store
	var morphismExecutor *morphism.Executor
	if cfg.DatabaseURL != "" {
		store, err := container.NewStore(cfg.DatabaseURL)
		if err != nil {
			logger.Error("failed to initialize container store", "error", err)
			os.Exit(1)
		}
		containerStore = store
		morphismExecutor = morphism.NewExecutor(containerStore, "urn:moos:actor:system")
		defer func() {
			_ = containerStore.Close()
		}()
	}

	mux := newMuxWithAuthAndExecutor(containerStore, cfg.BearerToken, morphismExecutor)
	dispatcher := model.NewDispatcher(
		cfg.ModelProvider,
		model.AnthropicAdapter{},
		model.GeminiAdapter{},
		model.OpenAIAdapter{},
	)
	mcpBridge := tool.NewMCPBridge(tool.NewRegistryWithContainerStore(containerStore), tool.DefaultPolicy())
	mcpBroker := newMCPSessionBroker()
	attachMCPRoutes(mux, mcpBridge, mcpBroker, cfg.BearerToken)
	sessionStore, storeErr := session.NewStoreWithFallback(cfg.RedisURL, cfg.SessionTTL)
	if storeErr != nil {
		logger.Warn("session store fallback activated", "error", storeErr)
	}
	sessionManager := session.NewManagerWithStore(morphismExecutor, dispatcher, cfg.SessionTTL, cfg.SessionCleanupEvery, logger, sessionStore)
	sessionManager.SetToolDispatcher(tool.NewRunner(cfg.ToolRuntimeAddr, 5*time.Second))
	defer sessionManager.Shutdown()
	wsGateway := newWebSocketGateway(morphismExecutor, sessionManager, cfg.BearerToken, logger)

	server := &http.Server{
		Addr:              cfg.HTTPAddr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	wsServer := &http.Server{
		Addr:              cfg.WebSocketAddr,
		Handler:           wsGateway,
		ReadHeaderTimeout: 5 * time.Second,
	}

	errCh := make(chan error, 2)
	go func() {
		logger.Info("kernel http starting", "addr", cfg.HTTPAddr)
		errCh <- server.ListenAndServe()
	}()
	go func() {
		logger.Info("kernel websocket starting", "addr", cfg.WebSocketAddr)
		errCh <- wsServer.ListenAndServe()
	}()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	select {
	case sig := <-sigCh:
		logger.Info("shutdown signal received", "signal", sig.String())
	case err := <-errCh:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			logger.Error("kernel server failed", "error", err)
			os.Exit(1)
		}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := server.Shutdown(ctx); err != nil {
		logger.Error("graceful shutdown failed", "error", err)
		os.Exit(1)
	}
	if err := wsServer.Shutdown(ctx); err != nil {
		logger.Error("websocket graceful shutdown failed", "error", err)
		os.Exit(1)
	}
	logger.Info("kernel stopped")
}

func newMux(containerStore containerStoreAPI) *http.ServeMux {
	return newMuxWithAuthAndExecutor(containerStore, "", nil)
}

func newMuxWithAuth(containerStore containerStoreAPI, bearerToken string) *http.ServeMux {
	return newMuxWithAuthAndExecutor(containerStore, bearerToken, nil)
}

func newMuxWithAuthAndExecutor(containerStore containerStoreAPI, bearerToken string, executor *morphism.Executor) *http.ServeMux {
	mux := http.NewServeMux()
	morphismExecutor := executor
	if morphismExecutor == nil && containerStore != nil {
		morphismExecutor = morphism.NewExecutor(containerStore, "urn:moos:actor:system")
	}
	mux.HandleFunc("/health", func(writer http.ResponseWriter, request *http.Request) {
		writer.WriteHeader(http.StatusOK)
		_, _ = writer.Write([]byte("ok"))
	})
	mux.HandleFunc("/health/db", func(writer http.ResponseWriter, request *http.Request) {
		if containerStore == nil {
			writer.WriteHeader(http.StatusNotImplemented)
			_, _ = writer.Write([]byte("database not configured"))
			return
		}
		ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
		defer cancel()
		if err := containerStore.Health(ctx); err != nil {
			writer.WriteHeader(http.StatusServiceUnavailable)
			_, _ = writer.Write([]byte("db unavailable"))
			return
		}
		writer.WriteHeader(http.StatusOK)
		_, _ = writer.Write([]byte("ok"))
	})
	mux.HandleFunc("/api/v1/morphisms", func(writer http.ResponseWriter, request *http.Request) {
		if !authorizeAPIRequest(writer, request, bearerToken) {
			return
		}
		if request.Method != http.MethodPost {
			writer.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if containerStore == nil {
			writer.WriteHeader(http.StatusNotImplemented)
			_, _ = writer.Write([]byte("database not configured"))
			return
		}

		body, readErr := io.ReadAll(io.LimitReader(request.Body, 1<<20))
		if readErr != nil {
			writer.WriteHeader(http.StatusBadRequest)
			_, _ = writer.Write([]byte("invalid request body"))
			return
		}

		var envelope morphism.Envelope
		if err := json.Unmarshal(body, &envelope); err != nil {
			writer.WriteHeader(http.StatusBadRequest)
			_, _ = writer.Write([]byte("invalid json payload"))
			return
		}

		ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
		defer cancel()
		nextVersion, err := morphismExecutor.Apply(ctx, envelope)
		if err != nil {
			if errors.Is(err, morphism.ErrInvalidEnvelope) {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("invalid morphism envelope"))
				return
			}
			if errors.Is(err, container.ErrNotFound) {
				writer.WriteHeader(http.StatusNotFound)
				_, _ = writer.Write([]byte("container not found"))
				return
			}
			if errors.Is(err, container.ErrAlreadyExists) {
				writer.WriteHeader(http.StatusConflict)
				_, _ = writer.Write([]byte("resource already exists"))
				return
			}
			if errors.Is(err, container.ErrVersionConflict) {
				writer.Header().Set("X-Current-Version", strconv.FormatInt(nextVersion, 10))
				writer.WriteHeader(http.StatusConflict)
				_, _ = writer.Write([]byte("version conflict"))
				return
			}
			writer.WriteHeader(http.StatusInternalServerError)
			_, _ = writer.Write([]byte("failed to apply morphism"))
			return
		}

		writer.WriteHeader(http.StatusAccepted)
	})
	mux.HandleFunc("/api/v1/morphisms/log", func(writer http.ResponseWriter, request *http.Request) {
		if !authorizeAPIRequest(writer, request, bearerToken) {
			return
		}
		if request.Method != http.MethodGet {
			writer.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if containerStore == nil {
			writer.WriteHeader(http.StatusNotImplemented)
			_, _ = writer.Write([]byte("database not configured"))
			return
		}

		limit := 50
		if limitQuery := strings.TrimSpace(request.URL.Query().Get("limit")); limitQuery != "" {
			parsed, parseErr := strconv.Atoi(limitQuery)
			if parseErr != nil || parsed <= 0 {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("limit must be a positive integer"))
				return
			}
			limit = parsed
		}

		query := container.MorphismLogQuery{
			ScopeURN: strings.TrimSpace(request.URL.Query().Get("scope_urn")),
			Type:     strings.ToUpper(strings.TrimSpace(request.URL.Query().Get("type"))),
			Limit:    limit,
		}

		ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
		defer cancel()
		entries, err := containerStore.ListMorphismLog(ctx, query)
		if err != nil {
			writer.WriteHeader(http.StatusInternalServerError)
			_, _ = writer.Write([]byte("failed to query morphism log"))
			return
		}

		writer.Header().Set("Content-Type", "application/json")
		writer.Header().Set("X-Log-Count", strconv.Itoa(len(entries)))
		writer.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(writer).Encode(entries)
	})
	mux.HandleFunc("/api/v1/containers", func(writer http.ResponseWriter, request *http.Request) {
		if !authorizeAPIRequest(writer, request, bearerToken) {
			return
		}
		if request.Method != http.MethodPost {
			writer.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if containerStore == nil {
			writer.WriteHeader(http.StatusNotImplemented)
			_, _ = writer.Write([]byte("database not configured"))
			return
		}

		body, readErr := io.ReadAll(io.LimitReader(request.Body, 1<<20))
		if readErr != nil {
			writer.WriteHeader(http.StatusBadRequest)
			_, _ = writer.Write([]byte("invalid request body"))
			return
		}
		var record container.Record
		if err := json.Unmarshal(body, &record); err != nil {
			writer.WriteHeader(http.StatusBadRequest)
			_, _ = writer.Write([]byte("invalid json payload"))
			return
		}
		if strings.TrimSpace(record.URN) == "" {
			writer.WriteHeader(http.StatusBadRequest)
			_, _ = writer.Write([]byte("container urn is required"))
			return
		}

		ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
		defer cancel()
		if err := morphismExecutor.Add(ctx, record); err != nil {
			writer.WriteHeader(http.StatusInternalServerError)
			_, _ = writer.Write([]byte("failed to create container"))
			return
		}

		writer.WriteHeader(http.StatusCreated)
	})
	mux.HandleFunc("/api/v1/containers/", func(writer http.ResponseWriter, request *http.Request) {
		if !authorizeAPIRequest(writer, request, bearerToken) {
			return
		}
		if request.Method != http.MethodGet && request.Method != http.MethodPatch && request.Method != http.MethodPost && request.Method != http.MethodDelete {
			writer.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		if containerStore == nil {
			writer.WriteHeader(http.StatusNotImplemented)
			_, _ = writer.Write([]byte("database not configured"))
			return
		}

		raw := strings.TrimPrefix(request.URL.Path, "/api/v1/containers/")
		raw = strings.TrimSpace(raw)

		if strings.HasSuffix(raw, "/tree") {
			rootURN := strings.TrimSuffix(raw, "/tree")
			rootURN = strings.TrimSuffix(rootURN, "/")
			rootURN = strings.TrimSpace(rootURN)
			if rootURN == "" {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("root urn is required"))
				return
			}

			ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
			defer cancel()
			records, err := containerStore.TreeTraversal(ctx, rootURN)
			if err != nil {
				if errors.Is(err, container.ErrNotFound) {
					writer.WriteHeader(http.StatusNotFound)
					_, _ = writer.Write([]byte("container not found"))
					return
				}
				writer.WriteHeader(http.StatusInternalServerError)
				_, _ = writer.Write([]byte("failed to traverse tree"))
				return
			}

			writer.Header().Set("Content-Type", "application/json")
			writer.Header().Set("X-Tree-Count", strconv.Itoa(len(records)))
			writer.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(writer).Encode(records)
			return
		}

		if strings.HasSuffix(raw, "/wires") {
			fromURN := strings.TrimSuffix(raw, "/wires")
			fromURN = strings.TrimSuffix(fromURN, "/")
			fromURN = strings.TrimSpace(fromURN)
			if fromURN == "" {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("container urn is required"))
				return
			}
			if request.Method != http.MethodPost && request.Method != http.MethodDelete {
				writer.WriteHeader(http.StatusMethodNotAllowed)
				return
			}

			body, readErr := io.ReadAll(io.LimitReader(request.Body, 1<<20))
			if readErr != nil {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("invalid request body"))
				return
			}
			var payload wireRequest
			if err := json.Unmarshal(body, &payload); err != nil {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("invalid json payload"))
				return
			}
			if strings.TrimSpace(payload.FromPort) == "" || strings.TrimSpace(payload.ToURN) == "" || strings.TrimSpace(payload.ToPort) == "" {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("from_port, to_urn, and to_port are required"))
				return
			}

			wire := container.WireRecord{
				FromContainerURN: fromURN,
				FromPort:         payload.FromPort,
				ToContainerURN:   payload.ToURN,
				ToPort:           payload.ToPort,
				MetadataJSON:     payload.MetadataJSON,
			}

			ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
			defer cancel()

			if request.Method == http.MethodPost {
				err := morphismExecutor.Link(ctx, wire)
				if err != nil {
					if errors.Is(err, container.ErrAlreadyExists) {
						writer.WriteHeader(http.StatusConflict)
						_, _ = writer.Write([]byte("wire already exists"))
						return
					}
					if errors.Is(err, container.ErrNotFound) {
						writer.WriteHeader(http.StatusNotFound)
						_, _ = writer.Write([]byte("container not found"))
						return
					}
					writer.WriteHeader(http.StatusInternalServerError)
					_, _ = writer.Write([]byte("failed to create wire"))
					return
				}

				writer.WriteHeader(http.StatusCreated)
				return
			}

			err := morphismExecutor.Unlink(ctx, wire)
			if err != nil {
				if errors.Is(err, container.ErrNotFound) {
					writer.WriteHeader(http.StatusNotFound)
					_, _ = writer.Write([]byte("wire not found"))
					return
				}
				writer.WriteHeader(http.StatusInternalServerError)
				_, _ = writer.Write([]byte("failed to delete wire"))
				return
			}

			writer.WriteHeader(http.StatusNoContent)
			return
		}

		if request.Method == http.MethodPatch {
			urn := strings.TrimSuffix(raw, "/")
			urn = strings.TrimSpace(urn)
			if urn == "" {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("container urn is required"))
				return
			}

			body, readErr := io.ReadAll(io.LimitReader(request.Body, 1<<20))
			if readErr != nil {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("invalid request body"))
				return
			}
			var payload mutateKernelRequest
			if err := json.Unmarshal(body, &payload); err != nil {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("invalid json payload"))
				return
			}
			if payload.ExpectedVersion <= 0 {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("expected_version must be > 0"))
				return
			}

			ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
			defer cancel()
			nextVersion, err := morphismExecutor.Mutate(ctx, urn, payload.ExpectedVersion, payload.KernelJSON)
			if err != nil {
				if errors.Is(err, container.ErrNotFound) {
					writer.WriteHeader(http.StatusNotFound)
					_, _ = writer.Write([]byte("container not found"))
					return
				}
				if errors.Is(err, container.ErrVersionConflict) {
					writer.Header().Set("X-Current-Version", strconv.FormatInt(nextVersion, 10))
					writer.WriteHeader(http.StatusConflict)
					_, _ = writer.Write([]byte("version conflict"))
					return
				}
				writer.WriteHeader(http.StatusInternalServerError)
				_, _ = writer.Write([]byte("failed to mutate container"))
				return
			}

			writer.Header().Set("Content-Type", "application/json")
			writer.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(writer).Encode(mutateKernelResponse{URN: urn, Version: nextVersion})
			return
		}

		if strings.HasSuffix(raw, "/children") {
			parentURN := strings.TrimSuffix(raw, "/children")
			parentURN = strings.TrimSuffix(parentURN, "/")
			parentURN = strings.TrimSpace(parentURN)
			if parentURN == "" {
				writer.WriteHeader(http.StatusBadRequest)
				_, _ = writer.Write([]byte("parent urn is required"))
				return
			}
			ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
			defer cancel()
			records, err := containerStore.ListChildren(ctx, parentURN)
			if err != nil {
				writer.WriteHeader(http.StatusInternalServerError)
				_, _ = writer.Write([]byte("failed to list children"))
				return
			}

			writer.Header().Set("Content-Type", "application/json")
			writer.Header().Set("X-Children-Count", strconv.Itoa(len(records)))
			writer.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(writer).Encode(records)
			return
		}

		urn := raw
		if urn == "" {
			writer.WriteHeader(http.StatusBadRequest)
			_, _ = writer.Write([]byte("container urn is required"))
			return
		}

		ctx, cancel := context.WithTimeout(request.Context(), 2*time.Second)
		defer cancel()
		record, err := containerStore.GetByURN(ctx, urn)
		if err != nil {
			if errors.Is(err, container.ErrNotFound) {
				writer.WriteHeader(http.StatusNotFound)
				_, _ = writer.Write([]byte("container not found"))
				return
			}
			writer.WriteHeader(http.StatusInternalServerError)
			_, _ = writer.Write([]byte("failed to read container"))
			return
		}

		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(writer).Encode(record)
	})

	return mux
}

func authorizeAPIRequest(writer http.ResponseWriter, request *http.Request, bearerToken string) bool {
	if strings.TrimSpace(bearerToken) == "" {
		return true
	}
	authorizationHeader := strings.TrimSpace(request.Header.Get("Authorization"))
	expected := "Bearer " + bearerToken
	if authorizationHeader != expected {
		writer.Header().Set("WWW-Authenticate", "Bearer")
		writer.WriteHeader(http.StatusUnauthorized)
		_, _ = writer.Write([]byte("unauthorized"))
		return false
	}
	return true
}

type mcpSessionBroker struct {
	register   chan mcpBrokerRegistration
	unregister chan string
	publish    chan mcpBrokerEvent

	inflightMu sync.Mutex
	inflight   map[string]context.CancelFunc
}

type mcpBrokerRegistration struct {
	sessionID string
	channel   chan []byte
}

type mcpBrokerEvent struct {
	sessionID string
	payload   []byte
}

func newMCPSessionBroker() *mcpSessionBroker {
	broker := &mcpSessionBroker{
		register:   make(chan mcpBrokerRegistration),
		unregister: make(chan string),
		publish:    make(chan mcpBrokerEvent, 128),
		inflight:   map[string]context.CancelFunc{},
	}
	go broker.run()
	return broker
}

func (broker *mcpSessionBroker) run() {
	subscribers := map[string]chan []byte{}
	for {
		select {
		case registration := <-broker.register:
			if existing, ok := subscribers[registration.sessionID]; ok {
				close(existing)
			}
			subscribers[registration.sessionID] = registration.channel
		case sessionID := <-broker.unregister:
			if channel, ok := subscribers[sessionID]; ok {
				close(channel)
				delete(subscribers, sessionID)
			}
		case event := <-broker.publish:
			channel, ok := subscribers[event.sessionID]
			if !ok {
				continue
			}
			select {
			case channel <- event.payload:
			default:
			}
		}
	}
}

func (broker *mcpSessionBroker) Subscribe(sessionID string) <-chan []byte {
	channel := make(chan []byte, 64)
	broker.register <- mcpBrokerRegistration{sessionID: sessionID, channel: channel}
	return channel
}

func (broker *mcpSessionBroker) Unsubscribe(sessionID string) {
	broker.unregister <- sessionID
}

func (broker *mcpSessionBroker) Publish(sessionID string, payload []byte) {
	if strings.TrimSpace(sessionID) == "" || len(payload) == 0 {
		return
	}
	broker.publish <- mcpBrokerEvent{sessionID: sessionID, payload: payload}
}

func (broker *mcpSessionBroker) RegisterInflight(sessionID string, id json.RawMessage, cancel context.CancelFunc) {
	if cancel == nil {
		return
	}
	key := mcpInflightKey(sessionID, id)
	if key == "" {
		return
	}
	broker.inflightMu.Lock()
	broker.inflight[key] = cancel
	broker.inflightMu.Unlock()
}

func (broker *mcpSessionBroker) ClearInflight(sessionID string, id json.RawMessage) {
	key := mcpInflightKey(sessionID, id)
	if key == "" {
		return
	}
	broker.inflightMu.Lock()
	delete(broker.inflight, key)
	broker.inflightMu.Unlock()
}

func (broker *mcpSessionBroker) CancelInflight(sessionID string, id json.RawMessage) bool {
	key := mcpInflightKey(sessionID, id)
	if key == "" {
		return false
	}
	broker.inflightMu.Lock()
	cancel, ok := broker.inflight[key]
	if ok {
		delete(broker.inflight, key)
	}
	broker.inflightMu.Unlock()
	if ok {
		cancel()
		return true
	}
	return false
}

func mcpInflightKey(sessionID string, id json.RawMessage) string {
	normalizedSession := strings.TrimSpace(sessionID)
	normalizedID := strings.TrimSpace(string(id))
	if normalizedSession == "" || normalizedID == "" || normalizedID == "null" {
		return ""
	}
	return normalizedSession + "::" + normalizedID
}

func attachMCPRoutes(mux *http.ServeMux, bridge *tool.MCPBridge, broker *mcpSessionBroker, bearerToken string) {
	handleMCPMessageRequest := func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost {
			writer.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		sessionID := strings.TrimSpace(request.URL.Query().Get("sessionId"))
		if sessionID == "" {
			sessionID = strings.TrimSpace(request.Header.Get("X-MCP-Session-ID"))
		}
		if sessionID == "" {
			writeMCPError(writer, nil, -32000, "sessionId is required")
			return
		}

		body, readErr := io.ReadAll(io.LimitReader(request.Body, 1<<20))
		if readErr != nil {
			writeMCPError(writer, nil, -32700, "invalid request body")
			return
		}

		var message jsonRPCMessage
		if err := json.Unmarshal(body, &message); err != nil {
			writeMCPError(writer, nil, -32700, "invalid json payload")
			return
		}
		broker.Publish(sessionID, mustEncodeMCPEvent("request", map[string]any{
			"session_id": sessionID,
			"message":    message,
		}))

		switch message.Method {
		case "initialize":
			result := map[string]any{
				"protocolVersion": "2024-11-05",
				"serverInfo":      map[string]any{"name": "moos-kernel", "version": "0.1.0"},
				"capabilities":    map[string]any{"tools": map[string]any{}, "resources": map[string]any{}},
				"sessionId":       sessionID,
			}
			writeMCPResult(writer, message.ID, result)
			broker.Publish(sessionID, mustEncodeMCPEvent("response", map[string]any{"id": message.ID, "method": message.Method, "result": result}))
		case "notifications/initialized":
			result := map[string]any{"acknowledged": true}
			writeMCPResult(writer, message.ID, result)
			broker.Publish(sessionID, mustEncodeMCPEvent("initialized", map[string]any{"sessionId": sessionID}))
		case "ping":
			result := map[string]any{"pong": true, "sessionId": sessionID}
			writeMCPResult(writer, message.ID, result)
			broker.Publish(sessionID, mustEncodeMCPEvent("response", map[string]any{"id": message.ID, "method": message.Method, "result": result}))
		case "tools/list":
			result := map[string]any{"tools": bridge.ToolsList()}
			writeMCPResult(writer, message.ID, result)
			broker.Publish(sessionID, mustEncodeMCPEvent("response", map[string]any{"id": message.ID, "method": message.Method, "result": result}))
		case "resources/list":
			result := map[string]any{"resources": bridge.ResourcesList()}
			writeMCPResult(writer, message.ID, result)
			broker.Publish(sessionID, mustEncodeMCPEvent("response", map[string]any{"id": message.ID, "method": message.Method, "result": result}))
		case "resources/read":
			var params struct {
				URI string `json:"uri"`
			}
			if err := json.Unmarshal(message.Params, &params); err != nil || strings.TrimSpace(params.URI) == "" {
				writeMCPError(writer, message.ID, -32602, "invalid resources/read params")
				broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32602, "message": "invalid resources/read params"}))
				return
			}
			resource, err := bridge.ResourcesRead(params.URI)
			if err != nil {
				writeMCPError(writer, message.ID, -32000, err.Error())
				broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32000, "message": err.Error()}))
				return
			}
			writeMCPResult(writer, message.ID, resource)
			broker.Publish(sessionID, mustEncodeMCPEvent("response", map[string]any{"id": message.ID, "method": message.Method, "result": resource}))
		case "tools/call":
			var params struct {
				Name      string         `json:"name"`
				Arguments map[string]any `json:"arguments"`
			}
			if err := json.Unmarshal(message.Params, &params); err != nil || strings.TrimSpace(params.Name) == "" {
				writeMCPError(writer, message.ID, -32602, "invalid tools/call params")
				broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32602, "message": "invalid tools/call params"}))
				return
			}
			if params.Arguments == nil {
				params.Arguments = map[string]any{}
			}
			callCtx, cancel := context.WithCancel(request.Context())
			broker.RegisterInflight(sessionID, message.ID, cancel)
			defer broker.ClearInflight(sessionID, message.ID)
			defer cancel()

			result, err := bridge.ToolsCall(callCtx, params.Name, params.Arguments)
			if err != nil {
				writeMCPError(writer, message.ID, -32000, err.Error())
				broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32000, "message": err.Error()}))
				return
			}
			writeMCPResult(writer, message.ID, result)
			broker.Publish(sessionID, mustEncodeMCPEvent("response", map[string]any{"id": message.ID, "method": message.Method, "result": result}))
		case "$/cancelRequest", "notifications/cancelled":
			var params map[string]json.RawMessage
			if err := json.Unmarshal(message.Params, &params); err != nil {
				writeMCPError(writer, message.ID, -32602, "invalid cancel params")
				broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32602, "message": "invalid cancel params"}))
				return
			}

			targetID := params["id"]
			if len(targetID) == 0 {
				targetID = params["requestId"]
			}
			if len(targetID) == 0 || strings.TrimSpace(string(targetID)) == "null" {
				writeMCPError(writer, message.ID, -32602, "cancel requires id or requestId")
				broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32602, "message": "cancel requires id or requestId"}))
				return
			}

			cancelled := broker.CancelInflight(sessionID, targetID)
			result := map[string]any{"cancelled": cancelled, "requestId": json.RawMessage(targetID)}
			writeMCPResult(writer, message.ID, result)
			if cancelled {
				broker.Publish(sessionID, mustEncodeMCPEvent("cancelled", map[string]any{"requestId": json.RawMessage(targetID), "sessionId": sessionID}))
			}
		default:
			writeMCPError(writer, message.ID, -32601, "method not found")
			broker.Publish(sessionID, mustEncodeMCPEvent("error", map[string]any{"id": message.ID, "method": message.Method, "code": -32601, "message": "method not found"}))
		}
	}

	handleMCPSSE := func(writer http.ResponseWriter, request *http.Request) {
		if !authorizeAPIRequest(writer, request, bearerToken) {
			return
		}
		if request.Method == http.MethodPost {
			handleMCPMessageRequest(writer, request)
			return
		}
		if request.Method != http.MethodGet {
			writer.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		sessionID := strings.TrimSpace(request.URL.Query().Get("sessionId"))
		if sessionID == "" {
			sessionID = newMCPSessionID()
		}
		updates := broker.Subscribe(sessionID)
		defer broker.Unsubscribe(sessionID)

		writer.Header().Set("Content-Type", "text/event-stream")
		writer.Header().Set("Cache-Control", "no-cache")
		writer.Header().Set("Connection", "keep-alive")
		writer.WriteHeader(http.StatusOK)
		_, _ = writer.Write([]byte("event: endpoint\n"))
		endpoint := fmt.Sprintf("{\"messages\":\"/mcp/messages?sessionId=%s\",\"sessionId\":\"%s\"}", sessionID, sessionID)
		_, _ = writer.Write([]byte("data: " + endpoint + "\n\n"))
		flusher, ok := writer.(http.Flusher)
		if !ok {
			return
		}
		flusher.Flush()

		keepAlive := time.NewTicker(15 * time.Second)
		defer keepAlive.Stop()
		for {
			select {
			case <-request.Context().Done():
				return
			case payload, ok := <-updates:
				if !ok {
					return
				}
				_, _ = writer.Write(payload)
				_, _ = writer.Write([]byte("\n\n"))
				flusher.Flush()
			case <-keepAlive.C:
				_, _ = writer.Write([]byte(": keep-alive\n\n"))
				flusher.Flush()
			}
		}
	}

	handleMCPMessages := func(writer http.ResponseWriter, request *http.Request) {
		if !authorizeAPIRequest(writer, request, bearerToken) {
			return
		}
		handleMCPMessageRequest(writer, request)
	}

	mux.HandleFunc("/mcp/sse", handleMCPSSE)
	mux.HandleFunc("/mcp/messages", handleMCPMessages)
	mux.HandleFunc("/mcp/message", handleMCPMessages)
	mux.HandleFunc("/sse", handleMCPSSE)
	mux.HandleFunc("/messages", handleMCPMessages)
	mux.HandleFunc("/message", handleMCPMessages)
}

func mustEncodeMCPEvent(eventType string, payload map[string]any) []byte {
	encoded, err := json.Marshal(payload)
	if err != nil {
		encoded = []byte(`{"error":"encode_failed"}`)
	}
	return []byte("event: " + eventType + "\n" + "data: " + string(encoded))
}

func newMCPSessionID() string {
	raw := make([]byte, 12)
	if _, err := rand.Read(raw); err != nil {
		return fmt.Sprintf("mcp-%d", time.Now().UTC().UnixNano())
	}
	return fmt.Sprintf("mcp-%x", raw)
}

func writeMCPResult(writer http.ResponseWriter, id json.RawMessage, result any) {
	if len(id) == 0 {
		id = json.RawMessage("null")
	}
	writer.Header().Set("Content-Type", "application/json")
	writer.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(writer).Encode(map[string]any{"jsonrpc": "2.0", "id": id, "result": result})
}

func writeMCPError(writer http.ResponseWriter, id json.RawMessage, code int, message string) {
	if len(id) == 0 {
		id = json.RawMessage("null")
	}
	writer.Header().Set("Content-Type", "application/json")
	writer.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(writer).Encode(map[string]any{
		"jsonrpc": "2.0",
		"id":      id,
		"error":   map[string]any{"code": code, "message": message},
	})
}
