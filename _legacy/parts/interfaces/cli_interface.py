"""
DeepAgent CLI Interface
=======================
Rich terminal interface for running DeepAgent or AgentSpec instances.

Provides:
- Interactive chat loop
- Streaming responses
- Workflow commands
- History management
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from pydantic_ai import Agent
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

if TYPE_CHECKING:
    from agent_factory.parts.templates.agent_spec import AgentSpec
    from agent_factory.parts.templates.deep_agent import DeepAgent

console = Console()


class DeepAgentCLI:
    """
    Rich terminal interface for DeepAgent or AgentSpec.

    Usage:
        # With DeepAgent
        agent = DeepAgent(name="MyAgent", model="gemini-2.0-flash", ...)
        cli = DeepAgentCLI(agent)
        await cli.run_interactive()

        # With AgentSpec
        spec = AgentSpec(...).load()
        cli = DeepAgentCLI.from_spec(spec)
        await cli.run_interactive()
    """

    def __init__(
        self,
        agent: "DeepAgent | Agent",
        name: str = "Agent",
        show_workflows: bool = True,
    ):
        """
        Initialize CLI with a DeepAgent or pydantic-ai Agent.

        Args:
            agent: DeepAgent instance or pydantic-ai Agent
            name: Display name for the agent
            show_workflows: Whether to show /workflows command
        """
        self.name = name
        self.show_workflows = show_workflows
        self.workflows: list[dict[str, Any]] = []

        # Handle both DeepAgent and raw pydantic-ai Agent
        if hasattr(agent, "_agent"):
            # DeepAgent wraps pydantic-ai Agent
            self._agent = agent._agent
            self._deep_agent = agent
        else:
            # Raw pydantic-ai Agent
            self._agent = agent
            self._deep_agent = None

    @classmethod
    def from_spec(
        cls,
        spec: "AgentSpec",
        context_section: str = "",
        name: Optional[str] = None,
    ) -> "DeepAgentCLI":
        """
        Create CLI from AgentSpec.

        Args:
            spec: Loaded AgentSpec instance
            context_section: Additional context to append to system prompt
            name: Override display name (defaults to spec.name)

        Returns:
            DeepAgentCLI instance ready to run
        """
        # Build system prompt
        system_prompt = spec.get_full_instructions()
        if context_section:
            system_prompt += f"\n\n{context_section}"

        # Create pydantic-ai Agent
        agent = Agent(
            model=spec.model,
            system_prompt=system_prompt,
        )

        # Create CLI
        cli = cls(agent, name=name or spec.name, show_workflows=bool(spec.workflows))
        cli.workflows = [
            {"name": wf.name, "description": wf.description, "triggers": wf.triggers}
            for wf in spec.workflows
        ]

        return cli

    def _show_startup(
        self,
        workspace: str = "",
        git_branch: str = "",
        model: str = "",
        extra_info: dict[str, Any] | None = None,
    ) -> None:
        """Display startup panel."""
        lines = [f"[bold green]🚀 {self.name} Ready[/]\n"]

        if workspace:
            lines.append(f"[bold]Workspace[/]: [cyan]{workspace}[/]")
        if git_branch:
            lines.append(f"[bold]Git branch[/]: [yellow]{git_branch}[/]")
        if model:
            lines.append(f"[bold]Model[/]: [magenta]{model}[/]")

        if extra_info:
            lines.append("")
            for key, value in extra_info.items():
                lines.append(f"[bold]{key}[/]: {value}")

        lines.append("")
        lines.append(
            "Type [bold red]'exit'[/] to quit"
            + (
                ", [bold blue]'/workflows'[/] to list workflows."
                if self.show_workflows
                else "."
            )
        )

        console.print(
            Panel(
                "\n".join(lines),
                title=f"Local UX - {self.name}",
                border_style="green",
            )
        )

    def _show_workflows(self) -> None:
        """Display available workflows."""
        if not self.workflows:
            console.print("[dim]No workflows loaded.[/]")
            return

        console.print("\n[bold]Available Workflows:[/]")
        for wf in self.workflows:
            triggers = ", ".join(wf.get("triggers", [])) or "none"
            console.print(
                f"  • [cyan]{wf['name']}[/] - {wf.get('description', '')} (triggers: {triggers})"
            )

    async def run_interactive(
        self,
        workspace: str = "",
        git_branch: str = "",
        model: str = "",
        extra_info: dict[str, Any] | None = None,
    ) -> None:
        """
        Run interactive chat loop.

        Args:
            workspace: Workspace path to display
            git_branch: Git branch to display
            model: Model name to display
            extra_info: Additional info to show in startup panel
        """
        self._show_startup(workspace, git_branch, model, extra_info)

        while True:
            try:
                user_input = Prompt.ask("\n[bold blue]You[/]")
            except (KeyboardInterrupt, EOFError):
                break

            if user_input.lower() in ("exit", "quit", "q"):
                break

            if user_input.lower() == "/workflows":
                self._show_workflows()
                continue

            if not user_input.strip():
                continue

            try:
                with console.status("[bold green]Thinking...[/]"):
                    result = await self._agent.run(user_input)

                # Render response as markdown
                response = str(result.data)
                console.print(f"\n[bold green]{self.name}[/]:")
                console.print(Markdown(response))

            except Exception as e:
                console.print(f"\n[bold red]Error[/]: {e}")

        console.print("\n[dim]Goodbye![/]")

    def run(
        self,
        workspace: str = "",
        git_branch: str = "",
        model: str = "",
        extra_info: dict[str, Any] | None = None,
    ) -> None:
        """Synchronous wrapper for run_interactive."""
        asyncio.run(self.run_interactive(workspace, git_branch, model, extra_info))
