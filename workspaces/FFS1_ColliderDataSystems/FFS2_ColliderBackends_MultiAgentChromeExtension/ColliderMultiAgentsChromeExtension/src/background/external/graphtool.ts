const GRAPHTOOL_URL = "ws://localhost:8001";

type MessageHandler = (data: Record<string, unknown>) => void;

export class GraphToolClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private endpoint: string;

  constructor(endpoint: "/ws/workflow" | "/ws/graph" = "/ws/workflow") {
    this.endpoint = endpoint;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${GRAPHTOOL_URL}${this.endpoint}`);

    this.ws.onopen = () => {
      console.log(`[GraphTool] Connected to ${this.endpoint}`);
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as Record<string, unknown>;
      const msgType = data.type as string;
      const listeners = this.handlers.get(msgType) ?? [];
      for (const handler of listeners) {
        handler(data);
      }
    };

    this.ws.onclose = () => {
      console.log(`[GraphTool] Disconnected from ${this.endpoint}`);
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.warn("[GraphTool] Not connected, queuing message");
      return;
    }
    this.ws.send(JSON.stringify(message));
  }

  on(messageType: string, handler: MessageHandler): void {
    const existing = this.handlers.get(messageType) ?? [];
    existing.push(handler);
    this.handlers.set(messageType, existing);
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 3000);
  }
}
