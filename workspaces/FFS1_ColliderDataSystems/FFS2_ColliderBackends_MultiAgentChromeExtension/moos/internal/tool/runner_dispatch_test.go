package tool

import (
	"context"
	"net"
	"testing"
	"time"

	"github.com/collider/moos/internal/model"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/structpb"
)

type streamOnlyRuntime struct{}

type streamRuntimeService interface {
	Execute(request *structpb.Struct, stream grpc.ServerStream) error
}

func (runtime *streamOnlyRuntime) Execute(request *structpb.Struct, stream grpc.ServerStream) error {
	_ = request
	response, err := structpb.NewStruct(map[string]any{"chunk": map[string]any{"status": "ok"}, "done": true})
	if err != nil {
		return err
	}
	return stream.SendMsg(response)
}

func registerStreamOnlyRuntime(server *grpc.Server, runtime *streamOnlyRuntime) {
	serviceDescription := &grpc.ServiceDesc{
		ServiceName: "moos.v1.ToolRuntime",
		HandlerType: (*streamRuntimeService)(nil),
		Streams: []grpc.StreamDesc{
			{
				StreamName:    "Execute",
				ServerStreams: true,
				Handler: func(srv any, stream grpc.ServerStream) error {
					request := new(structpb.Struct)
					if err := stream.RecvMsg(request); err != nil {
						return err
					}
					return runtime.Execute(request, stream)
				},
			},
		},
	}
	server.RegisterService(serviceDescription, runtime)
}

func TestRunnerDispatchUsesStreamingExecute(t *testing.T) {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	defer listener.Close()

	grpcServer := grpc.NewServer()
	registerStreamOnlyRuntime(grpcServer, &streamOnlyRuntime{})
	defer grpcServer.Stop()

	go func() {
		_ = grpcServer.Serve(listener)
	}()

	runner := NewRunner(listener.Addr().String(), 2*time.Second)
	result, dispatchErr := runner.Dispatch(context.Background(), "s_test", model.ToolCall{Name: "echo", Arguments: map[string]any{"x": 1}})
	if dispatchErr != nil {
		t.Fatalf("dispatch: %v", dispatchErr)
	}

	payload, ok := result.(map[string]any)
	if !ok {
		t.Fatalf("expected map result")
	}
	output, ok := payload["output"].(map[string]any)
	if !ok {
		t.Fatalf("expected output map, got %v", payload)
	}
	if output["status"] != "ok" {
		t.Fatalf("expected status=ok, got %v", output["status"])
	}
}
