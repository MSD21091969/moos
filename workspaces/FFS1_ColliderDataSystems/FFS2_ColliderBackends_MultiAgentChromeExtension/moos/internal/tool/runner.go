package tool

import (
	"context"
	"fmt"
	"time"

	"github.com/collider/moos/internal/model"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/structpb"
)

type Runner struct {
	address string
	timeout time.Duration
}

func NewRunner(address string, timeout time.Duration) *Runner {
	if timeout <= 0 {
		timeout = 5 * time.Second
	}
	return &Runner{address: address, timeout: timeout}
}

func (runner *Runner) Dispatch(ctx context.Context, sessionID string, call model.ToolCall) (any, error) {
	if runner.address == "" {
		return map[string]any{"status": "stubbed", "tool": call.Name, "arguments": call.Arguments, "session_id": sessionID}, nil
	}
	dialCtx, cancel := context.WithTimeout(ctx, runner.timeout)
	defer cancel()
	connection, err := grpc.DialContext(dialCtx, runner.address, grpc.WithTransportCredentials(insecure.NewCredentials()), grpc.WithBlock())
	if err != nil {
		return nil, err
	}
	defer connection.Close()

	request, err := structpb.NewStruct(map[string]any{"tool": call.Name, "arguments": call.Arguments, "session_id": sessionID})
	if err != nil {
		return nil, err
	}

	if streamed, streamErr := runner.invokeStreamExecute(ctx, connection, request); streamErr == nil {
		return streamed, nil
	}

	response := new(structpb.Struct)
	invokeCtx, invokeCancel := context.WithTimeout(ctx, runner.timeout)
	defer invokeCancel()
	if invokeErr := connection.Invoke(invokeCtx, "/moos.v1.ToolRuntime/ExecuteUnary", request, response); invokeErr != nil {
		return nil, invokeErr
	}
	return response.AsMap(), nil
}

func (runner *Runner) invokeStreamExecute(ctx context.Context, connection *grpc.ClientConn, request *structpb.Struct) (map[string]any, error) {
	invokeCtx, cancel := context.WithTimeout(ctx, runner.timeout)
	defer cancel()

	streamDescription := &grpc.StreamDesc{ServerStreams: true}
	stream, err := connection.NewStream(invokeCtx, streamDescription, "/moos.v1.ToolRuntime/Execute")
	if err != nil {
		return nil, err
	}
	if err := stream.SendMsg(request); err != nil {
		return nil, err
	}
	if err := stream.CloseSend(); err != nil {
		return nil, err
	}

	chunk := new(structpb.Struct)
	if err := stream.RecvMsg(chunk); err != nil {
		return nil, err
	}
	data := chunk.AsMap()
	if output, ok := data["chunk"].(map[string]any); ok {
		return map[string]any{"output": output}, nil
	}
	return data, nil
}

type MCPBridge struct {
	registry *Registry
	policy   Policy
}

func NewMCPBridge(registry *Registry, policy Policy) *MCPBridge {
	if registry == nil {
		registry = NewRegistry()
	}
	return &MCPBridge{registry: registry, policy: policy}
}

func (bridge *MCPBridge) ToolsList() []Definition {
	return bridge.registry.List()
}

func (bridge *MCPBridge) ToolsCall(ctx context.Context, name string, arguments map[string]any) (map[string]any, error) {
	raw, err := structpb.NewStruct(arguments)
	if err != nil {
		return nil, err
	}
	if err := bridge.policy.Validate(name, []byte(raw.String())); err != nil {
		return nil, err
	}
	callContext := ctx
	if bridge.policy.MaxExecutionMs > 0 {
		timeout := time.Duration(bridge.policy.MaxExecutionMs) * time.Millisecond
		var cancel context.CancelFunc
		callContext, cancel = context.WithTimeout(ctx, timeout)
		defer cancel()
	}
	result, runErr := bridge.registry.Execute(callContext, name, arguments)
	if runErr != nil {
		return nil, runErr
	}
	return map[string]any{"output": result}, nil
}

func (bridge *MCPBridge) ResourcesList() []map[string]any {
	definitions := bridge.registry.List()
	resources := make([]map[string]any, 0, len(definitions))
	for _, definition := range definitions {
		resources = append(resources, map[string]any{"uri": fmt.Sprintf("tool://%s", definition.Name), "name": definition.Name})
	}
	return resources
}

func (bridge *MCPBridge) ResourcesRead(uri string) (map[string]any, error) {
	return map[string]any{"uri": uri, "content": "resource payload placeholder"}, nil
}
