"""
Shared Chat Overlay Specification
=================================
Design specification for the unified chat overlay UI.

This document defines the interface that both:
- React (PilotOverlay.tsx) - for web frontends
- Python (textual) - for terminal UIs

Must implement to provide consistent user experience.

The UI is:
- Independent: Can be dropped into any app
- User-faced: Always visible, pilot guides user
- Context-aware: Shows current location (container/workspace)
- Movable: Can be positioned/minimized
- Transparent: Glass effect, doesn't block content
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OverlayPosition(str, Enum):
    """Where the overlay is positioned."""

    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    CENTER = "center"  # For modal mode


class OverlayState(str, Enum):
    """Current overlay state."""

    EXPANDED = "expanded"  # Full chat visible
    MINIMIZED = "minimized"  # Just icon/indicator
    HIDDEN = "hidden"  # Completely hidden


class Message(BaseModel):
    """Chat message structure - same for React and Python."""

    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # Optional metadata
    is_streaming: bool = False  # Currently streaming in
    tool_calls: list[dict] = Field(default_factory=list)  # Any tool invocations
    error: Optional[str] = None  # Error if any


class ContextInfo(BaseModel):
    """
    Current context displayed in overlay header.

    For Collider Pilots: container path, canvas name
    For Workspace Agents: cwd, git branch
    """

    primary: str  # Main context (container name / cwd)
    secondary: Optional[str] = None  # Secondary (canvas / git branch)
    breadcrumbs: list[str] = Field(default_factory=list)  # Navigation path
    type: str = "generic"  # "container" | "workspace" | "canvas"


class OverlayConfig(BaseModel):
    """
    Configuration for chat overlay.

    Same interface for both React and Python implementations.
    """

    # Identity
    title: str = "Pilot"  # "Collider Pilot" / "Workspace Agent"
    subtitle: str = "Ready to guide you"

    # Position/State
    position: OverlayPosition = OverlayPosition.BOTTOM_RIGHT
    initial_state: OverlayState = OverlayState.EXPANDED

    # Size
    width: int = 384  # pixels for React, columns for textual
    min_height: int = 300
    max_height: int = 600

    # Features
    show_context: bool = True  # Show context header
    show_connection_status: bool = True  # Show connected indicator
    enable_voice: bool = False  # Voice input (future)
    enable_minimize: bool = True  # Allow minimizing
    enable_drag: bool = False  # Allow dragging (future)

    # Behavior
    stream_responses: bool = True
    auto_scroll: bool = True
    persist_history: bool = True

    # Styling
    theme: str = "dark"  # "dark" | "light" | "system"
    blur_background: bool = True  # Glass effect
    border_radius: int = 16  # px


class OverlayCallbacks(BaseModel):
    """
    Callback interface for overlay events.

    Implementations wire these to actual handlers.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Message handling
    on_send_message: Optional[Callable[[str], None]] = None
    on_message_received: Optional[Callable[[Message], None]] = None

    # State changes
    on_state_change: Optional[Callable[[OverlayState], None]] = None
    on_position_change: Optional[Callable[[OverlayPosition], None]] = None

    # Context
    on_context_update: Optional[Callable[[ContextInfo], None]] = None

    # Lifecycle
    on_close: Optional[Callable[[], None]] = None
    on_clear_history: Optional[Callable[[], None]] = None


# =============================================================================
# Interface that implementations must follow
# =============================================================================


class ChatOverlayInterface:
    """
    Abstract interface for chat overlay implementations.

    Both React (TypeScript) and Python (textual) should implement
    this same interface for consistency.
    """

    def __init__(
        self,
        config: OverlayConfig,
        callbacks: OverlayCallbacks,
    ):
        """Initialize with config and callbacks."""
        self.config = config
        self.callbacks = callbacks
        self.messages: list[Message] = []
        self.state = config.initial_state
        self.context: Optional[ContextInfo] = None
        self.is_connected = False
        self.is_thinking = False

    # State management
    def set_state(self, state: OverlayState) -> None:
        """Change overlay state (expanded/minimized/hidden)."""
        self.state = state
        if self.callbacks.on_state_change:
            self.callbacks.on_state_change(state)

    def set_position(self, position: OverlayPosition) -> None:
        """Change overlay position."""
        self.config.position = position
        if self.callbacks.on_position_change:
            self.callbacks.on_position_change(position)

    # Context
    def update_context(self, context: ContextInfo) -> None:
        """Update displayed context."""
        self.context = context
        if self.callbacks.on_context_update:
            self.callbacks.on_context_update(context)

    # Connection
    def set_connected(self, connected: bool) -> None:
        """Set connection status indicator."""
        self.is_connected = connected

    # Messages
    def add_message(self, message: Message) -> None:
        """Add a message to the chat."""
        self.messages.append(message)
        if self.callbacks.on_message_received:
            self.callbacks.on_message_received(message)

    def set_thinking(self, thinking: bool) -> None:
        """Show/hide thinking indicator."""
        self.is_thinking = thinking

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages = []
        if self.callbacks.on_clear_history:
            self.callbacks.on_clear_history()

    # User input
    def send_message(self, content: str) -> None:
        """Handle user sending a message."""
        if self.callbacks.on_send_message:
            self.callbacks.on_send_message(content)

    # Render (implementation-specific)
    def render(self) -> Any:
        """
        Render the overlay.

        - React: Returns JSX element
        - Python/textual: Returns ComposeResult
        """
        raise NotImplementedError("Subclass must implement render()")


# =============================================================================
# TypeScript interface equivalent (for documentation)
# =============================================================================

TYPESCRIPT_INTERFACE = """
// TypeScript equivalent interface for React implementation

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  toolCalls?: ToolCall[];
  error?: string;
}

interface ContextInfo {
  primary: string;
  secondary?: string;
  breadcrumbs: string[];
  type: 'container' | 'workspace' | 'canvas' | 'generic';
}

interface OverlayConfig {
  title: string;
  subtitle: string;
  position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left' | 'center';
  initialState: 'expanded' | 'minimized' | 'hidden';
  width: number;
  minHeight: number;
  maxHeight: number;
  showContext: boolean;
  showConnectionStatus: boolean;
  enableVoice: boolean;
  enableMinimize: boolean;
  enableDrag: boolean;
  streamResponses: boolean;
  autoScroll: boolean;
  persistHistory: boolean;
  theme: 'dark' | 'light' | 'system';
  blurBackground: boolean;
  borderRadius: number;
}

interface OverlayCallbacks {
  onSendMessage?: (content: string) => void;
  onMessageReceived?: (message: Message) => void;
  onStateChange?: (state: OverlayState) => void;
  onPositionChange?: (position: OverlayPosition) => void;
  onContextUpdate?: (context: ContextInfo) => void;
  onClose?: () => void;
  onClearHistory?: () => void;
}

// React component props
interface ChatOverlayProps extends OverlayConfig, OverlayCallbacks {
  messages: Message[];
  context?: ContextInfo;
  isConnected: boolean;
  isThinking: boolean;
}
"""
