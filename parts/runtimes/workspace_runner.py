"""
Workspace Runner - TUI Interface
================================
Terminal User Interface for workspace agents using textual.

Provides a floating/independent chat overlay similar to frontend's
ColliderPilot but for terminal environments.

Features:
- Floating chat panel (can be toggled/minimized)
- Streaming responses
- Context-aware (shows workspace info)
- Works with any AgentSpec/WorkspaceAgent

Usage:
    from agent_factory.parts import get_part

    WorkspaceRunner = get_part("workspace_runner_v1")
    WorkspaceAgent = get_part("workspace_agent_v1")

    agent = WorkspaceAgent.from_workspace()
    runner = WorkspaceRunner(agent)
    runner.run()  # Opens TUI

    # Or headless mode
    response = await runner.chat("Hello")
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, AsyncGenerator, Callable
from datetime import datetime

from pydantic import BaseModel, Field

# Lazy import textual - it's optional for headless mode
try:
    from textual.app import App, ComposeResult
    from textual.widgets import Static, Input, Footer, Header, Label
    from textual.containers import Container, ScrollableContainer
    from textual.binding import Binding

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

from agent_factory.parts.agents.workspace_agent import WorkspaceAgent
from agent_factory.parts.config.settings import get_settings


class Message(BaseModel):
    """Chat message."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class WorkspaceRunnerConfig(BaseModel):
    """Configuration for the workspace runner."""

    # LLM settings (from settings or override)
    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 4096

    # UI settings
    show_context: bool = True
    stream_responses: bool = True
    save_history: bool = True
    history_file: Optional[Path] = None

    # Behavior
    confirm_dangerous: bool = True  # Confirm file writes, deletes
    sandbox_mode: bool = True  # Restrict to workspace


class WorkspaceRunner:
    """
    TUI/Headless runner for workspace agents.

    Can operate in two modes:
    1. TUI mode: Full textual interface with chat panel
    2. Headless mode: Programmatic chat without UI
    """

    def __init__(
        self,
        agent: WorkspaceAgent,
        config: Optional[WorkspaceRunnerConfig] = None,
        on_message: Optional[Callable[[Message], None]] = None,
    ):
        self.agent = agent
        self.config = config or WorkspaceRunnerConfig()
        self.on_message = on_message
        self.messages: list[Message] = []

        # Load API key from settings
        settings = get_settings()
        self._api_key = settings.get_secret("GEMINI_API_KEY")

    async def chat(self, user_input: str) -> str:
        """
        Send a message and get response (headless mode).

        Args:
            user_input: User message

        Returns:
            Assistant response
        """
        # Add user message
        user_msg = Message(role="user", content=user_input)
        self.messages.append(user_msg)
        self.agent.add_message("user", user_input)

        if self.on_message:
            self.on_message(user_msg)

        # Build prompt with context
        system_prompt = self.agent.get_system_prompt()

        # Call LLM (using google-generativeai for now)
        response = await self._call_llm(system_prompt, user_input)

        # Add assistant message
        assistant_msg = Message(role="assistant", content=response)
        self.messages.append(assistant_msg)
        self.agent.add_message("assistant", response)

        if self.on_message:
            self.on_message(assistant_msg)

        return response

    async def chat_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        Send a message and stream response tokens.

        Args:
            user_input: User message

        Yields:
            Response tokens as they arrive
        """
        # Add user message
        user_msg = Message(role="user", content=user_input)
        self.messages.append(user_msg)
        self.agent.add_message("user", user_input)

        if self.on_message:
            self.on_message(user_msg)

        system_prompt = self.agent.get_system_prompt()

        full_response = ""
        async for chunk in self._call_llm_stream(system_prompt, user_input):
            full_response += chunk
            yield chunk

        # Add complete message
        assistant_msg = Message(role="assistant", content=full_response)
        self.messages.append(assistant_msg)
        self.agent.add_message("assistant", full_response)

        if self.on_message:
            self.on_message(assistant_msg)

    async def _call_llm(self, system_prompt: str, user_input: str) -> str:
        """Call LLM and get complete response."""
        try:
            import google.generativeai as genai

            if not self._api_key:
                return "⚠️ No API key configured. Set GEMINI_API_KEY in secrets/api_keys.env"

            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(
                model_name=self.config.model,
                system_instruction=system_prompt,
            )

            response = model.generate_content(user_input)
            return response.text

        except ImportError:
            return "⚠️ google-generativeai not installed. Run: pip install google-generativeai"
        except Exception as e:
            return f"⚠️ Error: {e}"

    async def _call_llm_stream(
        self, system_prompt: str, user_input: str
    ) -> AsyncGenerator[str, None]:
        """Call LLM with streaming."""
        try:
            import google.generativeai as genai

            if not self._api_key:
                yield "⚠️ No API key configured. Set GEMINI_API_KEY in secrets/api_keys.env"
                return

            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(
                model_name=self.config.model,
                system_instruction=system_prompt,
            )

            response = model.generate_content(user_input, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except ImportError:
            yield "⚠️ google-generativeai not installed. Run: pip install google-generativeai"
        except Exception as e:
            yield f"⚠️ Error: {e}"

    def run(self) -> None:
        """
        Run the TUI interface.

        Requires textual to be installed.
        """
        if not TEXTUAL_AVAILABLE:
            raise ImportError(
                "textual not installed. Run: pip install textual\n"
                "Or use headless mode: await runner.chat('message')"
            )

        app = WorkspaceRunnerApp(self)
        app.run()

    def clear_history(self) -> None:
        """Clear chat history."""
        self.messages = []
        self.agent.clear_history()


# =============================================================================
# Textual TUI Application
# =============================================================================

if TEXTUAL_AVAILABLE:

    class MessageWidget(Static):
        """Single chat message widget."""

        def __init__(self, message: Message):
            self.message = message
            super().__init__()

        def compose(self) -> ComposeResult:
            role_label = "You" if self.message.role == "user" else "Agent"
            style = "bold cyan" if self.message.role == "user" else "bold green"

            yield Label(f"[{style}]{role_label}[/]")
            yield Static(self.message.content, classes="message-content")

    class ChatPanel(ScrollableContainer):
        """Scrollable chat history panel."""

        def __init__(self):
            super().__init__()
            self.messages: list[Message] = []

        def add_message(self, message: Message) -> None:
            self.messages.append(message)
            self.mount(MessageWidget(message))
            self.scroll_end(animate=False)

    class WorkspaceRunnerApp(App):
        """Textual app for workspace agent interaction."""

        CSS = """
        Screen {
            background: $surface;
        }
        
        #context-panel {
            height: 5;
            background: $primary-background;
            border: solid $primary;
            padding: 0 1;
        }
        
        #chat-panel {
            height: 1fr;
            background: $surface;
            border: solid $secondary;
            padding: 1;
        }
        
        .message-content {
            margin-left: 2;
            margin-bottom: 1;
        }
        
        #input-container {
            height: 3;
            background: $primary-background;
            padding: 0 1;
        }
        
        Input {
            width: 100%;
        }
        
        #thinking {
            text-style: italic;
            color: $text-muted;
        }
        """

        BINDINGS = [
            Binding("ctrl+c", "quit", "Quit"),
            Binding("ctrl+l", "clear", "Clear"),
            Binding("ctrl+r", "refresh_context", "Refresh"),
        ]

        def __init__(self, runner: WorkspaceRunner):
            super().__init__()
            self.runner = runner
            self.is_thinking = False

        def compose(self) -> ComposeResult:
            yield Header()

            # Context panel
            ctx = self.runner.agent.context
            context_text = (
                f"📁 {ctx.cwd.name}  "
                f"🌿 {ctx.git_branch or 'no git'}  "
                f"📍 {' > '.join(ctx.path_from_root) or 'root'}"
            )
            yield Static(context_text, id="context-panel")

            # Chat panel
            yield ChatPanel(id="chat-panel")

            # Input
            with Container(id="input-container"):
                yield Input(placeholder="Type a message...", id="user-input")

            yield Footer()

        async def on_input_submitted(self, event: Input.Submitted) -> None:
            """Handle user input."""
            if not event.value.strip() or self.is_thinking:
                return

            user_input = event.value
            event.input.value = ""

            # Add user message to chat
            chat_panel = self.query_one("#chat-panel", ChatPanel)
            user_msg = Message(role="user", content=user_input)
            chat_panel.add_message(user_msg)

            # Show thinking indicator
            self.is_thinking = True
            thinking = Static("⏳ Thinking...", id="thinking")
            chat_panel.mount(thinking)

            # Get response (streaming)
            full_response = ""
            response_widget = None

            async for chunk in self.runner.chat_stream(user_input):
                full_response += chunk

                if response_widget is None:
                    # Remove thinking indicator
                    thinking.remove()
                    # Create response widget
                    response_widget = Static(full_response, classes="message-content")
                    chat_panel.mount(Label("[bold green]Agent[/]"))
                    chat_panel.mount(response_widget)
                else:
                    response_widget.update(full_response)

                chat_panel.scroll_end(animate=False)

            self.is_thinking = False

        def action_clear(self) -> None:
            """Clear chat history."""
            self.runner.clear_history()
            chat_panel = self.query_one("#chat-panel", ChatPanel)
            chat_panel.remove_children()

        def action_refresh_context(self) -> None:
            """Refresh workspace context."""
            self.runner.agent.context = WorkspaceAgent._build_context(
                self.runner.agent.context.cwd,
                self.runner.agent.context.factory_root,
            )
            # Update context panel
            ctx = self.runner.agent.context
            context_text = (
                f"📁 {ctx.cwd.name}  "
                f"🌿 {ctx.git_branch or 'no git'}  "
                f"📍 {' > '.join(ctx.path_from_root) or 'root'}"
            )
            self.query_one("#context-panel", Static).update(context_text)


# =============================================================================
# Convenience functions
# =============================================================================


def create_workspace_runner(
    workspace_path: Optional[Path] = None,
    config: Optional[WorkspaceRunnerConfig] = None,
) -> WorkspaceRunner:
    """
    Create a workspace runner for the given directory.

    Args:
        workspace_path: Path to workspace (default: cwd)
        config: Runner configuration

    Returns:
        Configured WorkspaceRunner
    """
    agent = WorkspaceAgent.from_workspace(workspace_path)
    return WorkspaceRunner(agent, config)


async def quick_chat(message: str, workspace_path: Optional[Path] = None) -> str:
    """
    Quick one-shot chat without persistent runner.

    Args:
        message: User message
        workspace_path: Workspace path (default: cwd)

    Returns:
        Agent response
    """
    runner = create_workspace_runner(workspace_path)
    return await runner.chat(message)
