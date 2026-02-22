/**
 * NanoClawBridge Event Parser
 *
 * Transforms Claude Code CLI `--output-format stream-json` lines into
 * AgentEvent objects that match the protocol the Chrome Extension expects.
 *
 * Claude Code stream-json emits one JSON object per line. Key message types:
 *   { type: "assistant", message: { ... content blocks ... } }
 *   { type: "result",    subtype: "success" | "error", ... }
 *   { type: "system",    subtype: "init", ... }
 */

// ---------------------------------------------------------------------------
// AgentEvent — matches the Chrome Extension's expected event shapes
// ---------------------------------------------------------------------------

export type AgentEvent =
  | { kind: "text_delta"; text: string }
  | { kind: "tool_use_start"; name: string; args: string }
  | { kind: "tool_result"; name: string; result: string }
  | { kind: "thinking"; text: string }
  | { kind: "message_end" }
  | { kind: "error"; message: string };

// ---------------------------------------------------------------------------
// Claude Code stream-json shapes (subset we care about)
// ---------------------------------------------------------------------------

interface ContentBlockText {
  type: "text";
  text: string;
}

interface ContentBlockToolUse {
  type: "tool_use";
  id: string;
  name: string;
  input: Record<string, unknown>;
}

interface ContentBlockToolResult {
  type: "tool_result";
  tool_use_id: string;
  content: string | Array<{ type: string; text?: string }>;
}

interface ContentBlockThinking {
  type: "thinking";
  thinking: string;
}

type ContentBlock =
  | ContentBlockText
  | ContentBlockToolUse
  | ContentBlockToolResult
  | ContentBlockThinking;

interface StreamMessage {
  type: string;
  subtype?: string;
  message?: {
    role?: string;
    content?: ContentBlock[];
  };
  // For result messages
  result?: string;
  cost_usd?: number;
  duration_ms?: number;
  session_id?: string;
}

// ---------------------------------------------------------------------------
// Parser state — tracks what we've already emitted to produce deltas
// ---------------------------------------------------------------------------

export class EventParser {
  /** Index of the last content block we finished processing. */
  private lastBlockIndex = -1;
  /** Number of text characters already emitted for the current block. */
  private emittedTextLength = 0;

  /**
   * Parse a single JSON line from Claude Code's stream-json output.
   * Returns zero or more AgentEvents.
   */
  parse(line: string): AgentEvent[] {
    const trimmed = line.trim();
    if (!trimmed) return [];

    let msg: StreamMessage;
    try {
      msg = JSON.parse(trimmed) as StreamMessage;
    } catch {
      return [];
    }

    const events: AgentEvent[] = [];

    // Handle result/error events
    if (msg.type === "result") {
      if (msg.subtype === "error") {
        events.push({
          kind: "error",
          message: msg.result ?? "Claude Code returned an error",
        });
      }
      events.push({ kind: "message_end" });
      this.reset();
      return events;
    }

    // Handle assistant messages with content blocks
    if (msg.type === "assistant" && msg.message?.content) {
      const blocks = msg.message.content;

      for (let i = 0; i < blocks.length; i++) {
        const block = blocks[i];

        if (block.type === "text") {
          if (i > this.lastBlockIndex) {
            // New block — emit full text as delta
            if (block.text) {
              events.push({ kind: "text_delta", text: block.text });
            }
            this.lastBlockIndex = i;
            this.emittedTextLength = block.text.length;
          } else if (i === this.lastBlockIndex) {
            // Same block — emit only the new characters
            const newText = block.text.slice(this.emittedTextLength);
            if (newText) {
              events.push({ kind: "text_delta", text: newText });
              this.emittedTextLength = block.text.length;
            }
          }
        } else if (block.type === "tool_use" && i > this.lastBlockIndex) {
          events.push({
            kind: "tool_use_start",
            name: block.name,
            args: JSON.stringify(block.input),
          });
          this.lastBlockIndex = i;
          this.emittedTextLength = 0;
        } else if (block.type === "tool_result" && i > this.lastBlockIndex) {
          const resultText =
            typeof block.content === "string"
              ? block.content
              : block.content
                ?.map((c) => c.text ?? "")
                .join("\n") ?? "";
          events.push({
            kind: "tool_result",
            name: block.tool_use_id,
            result: resultText,
          });
          this.lastBlockIndex = i;
          this.emittedTextLength = 0;
        } else if (block.type === "thinking" && i > this.lastBlockIndex) {
          events.push({ kind: "thinking", text: block.thinking });
          this.lastBlockIndex = i;
          this.emittedTextLength = 0;
        }
      }
    }

    return events;
  }

  /** Reset parser state for a new message exchange. */
  reset(): void {
    this.lastBlockIndex = -1;
    this.emittedTextLength = 0;
  }
}
