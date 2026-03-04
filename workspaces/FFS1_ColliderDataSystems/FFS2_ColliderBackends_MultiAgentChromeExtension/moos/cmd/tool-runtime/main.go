package main

import (
	"context"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/collider/moos/internal/tool"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/reflection"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/structpb"
)

type runtimeServer struct {
	registry *tool.Registry
	policy   tool.Policy
}

type toolRuntimeService interface {
	ExecuteUnary(ctx context.Context, request *structpb.Struct) (*structpb.Struct, error)
	Execute(request *structpb.Struct, stream grpc.ServerStream) error
	List(ctx context.Context, request *structpb.Struct) (*structpb.Struct, error)
}

func main() {
	address := env("MOOS_TOOL_RUNTIME_ADDR", ":50052")
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))

	listener, err := net.Listen("tcp", address)
	if err != nil {
		logger.Error("failed to bind tool runtime", "error", err)
		os.Exit(1)
	}
	defer listener.Close()

	grpcServer := grpc.NewServer()
	service := &runtimeServer{registry: tool.NewRegistry(), policy: tool.DefaultPolicy()}
	registerToolRuntimeService(grpcServer, service)
	reflection.Register(grpcServer)

	errCh := make(chan error, 1)
	go func() {
		logger.Info("tool runtime starting", "addr", address)
		errCh <- grpcServer.Serve(listener)
	}()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	select {
	case sig := <-sigCh:
		logger.Info("tool runtime shutdown signal", "signal", sig.String())
	case serveErr := <-errCh:
		if serveErr != nil {
			logger.Error("tool runtime server failed", "error", serveErr)
			os.Exit(1)
		}
	}

	stopped := make(chan struct{})
	go func() {
		grpcServer.GracefulStop()
		close(stopped)
	}()
	select {
	case <-stopped:
	case <-time.After(5 * time.Second):
		grpcServer.Stop()
	}
	logger.Info("tool runtime stopped")
}

func (server *runtimeServer) ExecuteUnary(ctx context.Context, request *structpb.Struct) (*structpb.Struct, error) {
	payload := request.AsMap()
	toolName, _ := payload["tool"].(string)
	arguments, _ := payload["arguments"].(map[string]any)
	if arguments == nil {
		arguments = map[string]any{}
	}
	raw, _ := structpb.NewStruct(arguments)
	if err := server.policy.Validate(toolName, []byte(raw.String())); err != nil {
		return nil, status.Error(codes.InvalidArgument, err.Error())
	}
	result, err := server.registry.Execute(ctx, toolName, arguments)
	if err != nil {
		return nil, status.Error(codes.NotFound, err.Error())
	}
	response, marshalErr := structpb.NewStruct(map[string]any{"output": result})
	if marshalErr != nil {
		return nil, status.Error(codes.Internal, marshalErr.Error())
	}
	return response, nil
}

func (server *runtimeServer) Execute(request *structpb.Struct, stream grpc.ServerStream) error {
	payload := request.AsMap()
	toolName, _ := payload["tool"].(string)
	arguments, _ := payload["arguments"].(map[string]any)
	if arguments == nil {
		arguments = map[string]any{}
	}
	raw, _ := structpb.NewStruct(arguments)
	if err := server.policy.Validate(toolName, []byte(raw.String())); err != nil {
		return status.Error(codes.InvalidArgument, err.Error())
	}

	result, err := server.registry.Execute(stream.Context(), toolName, arguments)
	if err != nil {
		return status.Error(codes.NotFound, err.Error())
	}

	chunk, marshalErr := structpb.NewStruct(map[string]any{"chunk": result, "done": true})
	if marshalErr != nil {
		return status.Error(codes.Internal, marshalErr.Error())
	}
	if sendErr := stream.SendMsg(chunk); sendErr != nil {
		return sendErr
	}
	return nil
}

func (server *runtimeServer) List(ctx context.Context, request *structpb.Struct) (*structpb.Struct, error) {
	_ = ctx
	_ = request
	items := make([]any, 0)
	for _, definition := range server.registry.List() {
		items = append(items, map[string]any{"name": definition.Name, "description": definition.Description, "schema": definition.Schema})
	}
	response, err := structpb.NewStruct(map[string]any{"tools": items})
	if err != nil {
		return nil, status.Error(codes.Internal, err.Error())
	}
	return response, nil
}

func registerToolRuntimeService(server *grpc.Server, implementation *runtimeServer) {
	serviceDescription := &grpc.ServiceDesc{
		ServiceName: "moos.v1.ToolRuntime",
		HandlerType: (*toolRuntimeService)(nil),
		Methods: []grpc.MethodDesc{
			{
				MethodName: "ExecuteUnary",
				Handler: func(srv any, ctx context.Context, decoder func(any) error, interceptor grpc.UnaryServerInterceptor) (any, error) {
					request := new(structpb.Struct)
					if err := decoder(request); err != nil {
						return nil, err
					}
					if interceptor == nil {
						return implementation.ExecuteUnary(ctx, request)
					}
					info := &grpc.UnaryServerInfo{Server: srv, FullMethod: "/moos.v1.ToolRuntime/ExecuteUnary"}
					handler := func(ctx context.Context, req any) (any, error) {
						return implementation.ExecuteUnary(ctx, req.(*structpb.Struct))
					}
					return interceptor(ctx, request, info, handler)
				},
			},
			{
				MethodName: "List",
				Handler: func(srv any, ctx context.Context, decoder func(any) error, interceptor grpc.UnaryServerInterceptor) (any, error) {
					request := new(structpb.Struct)
					if err := decoder(request); err != nil {
						return nil, err
					}
					if interceptor == nil {
						return implementation.List(ctx, request)
					}
					info := &grpc.UnaryServerInfo{Server: srv, FullMethod: "/moos.v1.ToolRuntime/List"}
					handler := func(ctx context.Context, req any) (any, error) {
						return implementation.List(ctx, req.(*structpb.Struct))
					}
					return interceptor(ctx, request, info, handler)
				},
			},
		},
		Streams: []grpc.StreamDesc{
			{
				StreamName:    "Execute",
				ServerStreams: true,
				Handler: func(srv any, stream grpc.ServerStream) error {
					request := new(structpb.Struct)
					if err := stream.RecvMsg(request); err != nil {
						return err
					}
					return implementation.Execute(request, stream)
				},
			},
		},
	}
	server.RegisterService(serviceDescription, implementation)
}

func env(key string, fallback string) string {
	if value, ok := os.LookupEnv(key); ok && value != "" {
		return value
	}
	return fallback
}
