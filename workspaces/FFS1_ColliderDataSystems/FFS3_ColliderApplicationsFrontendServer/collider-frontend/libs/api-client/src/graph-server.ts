const DEFAULT_BASE_URL = "ws://localhost:8001";

type MessageHandler = (data: Record<string, unknown>) => void;

export class GraphServerClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  connect(endpoint: "/ws/workflow" | "/ws/graph" = "/ws/workflow"): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.ws = new WebSocket(`${this.baseUrl}${endpoint}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as Record<string, unknown>;
      const msgType = data.type as string;
      const listeners = this.handlers.get(msgType) ?? [];
      for (const handler of listeners) {
        handler(data);
      }
    };

    this.ws.onclose = () => {
      setTimeout(() => this.connect(endpoint), 3000);
    };
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }

  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    this.ws.send(JSON.stringify(message));
  }

  on(messageType: string, handler: MessageHandler): void {
    const existing = this.handlers.get(messageType) ?? [];
    existing.push(handler);
    this.handlers.set(messageType, existing);
  }

  executeWorkflow(workflowId: string, steps: string[]): void {
    this.send({
      type: "execute_workflow",
      workflow_id: workflowId,
      steps,
    });
  }
}
