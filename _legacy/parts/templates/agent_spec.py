"""
Generic Agent Specification Template
====================================
The unified pattern for agent configuration across Factory workspaces.

Supports both:
- L1 Workspace Agents: Read from .agent/ hierarchy (IDE, local CLI tools)
- L2 Application Pilots: Read from pilots/{id}/ folders (frontend, Gradio tools)

Folder Structure Convention:
    {agent_dir}/
    ├── __init__.py      (optional: AGENT_SPEC definition)
    ├── instructions.md  (system prompt - the "who you are")
    ├── rules/           (behavioral constraints - the "how you behave")
    │   └── *.md
    ├── workflows/       (task sequences - the "what you can do")
    │   └── *.md
    └── knowledge/       (domain context - the "what you know")
        └── *.md

This mirrors the pydantic-deep pattern:
- instructions.md → base system prompt
- rules/*.md → appended behavioral rules
- workflows/*.md → skill_directories equivalent
- knowledge/*.md → context/uploads equivalent
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SkillConfig(BaseModel):
    """Modular capability package for agents."""

    name: str  # "math-helper", "code-reviewer"
    path: str  # Path to skill definition
    recursive: bool = False  # Include subdirectories


class SubAgentConfig(BaseModel):
    """Delegation target for complex tasks."""

    name: str  # "researcher", "coder", "vision"
    description: str  # What this agent does
    triggers: list[str]  # Keywords that trigger delegation
    model: str = "gemini-2.0-flash"  # Model for this subagent
    instructions: str = ""  # Subagent-specific instructions


class WorkflowConfig(BaseModel):
    """Loaded workflow definition from workflows/*.md."""

    name: str
    description: str = ""
    triggers: list[str] = Field(default_factory=list)
    content: str = ""


class SummarizationConfig(BaseModel):
    """History compression settings for long conversations."""

    trigger_tokens: int = 8000  # When to summarize
    keep_messages: int = 10  # Messages to preserve verbatim


class AgentSpec(BaseModel):
    """
    Generic Agent Specification Template.

    The unified pattern for defining agents across the Factory.
    Used by both workspace agents (.agent/) and application pilots.

    Two modes of operation:
    1. Inline: Instructions provided as string (quick/testing)
    2. Dynamic: Instructions loaded from agent_dir folder (production)

    Example:
        # Mode 1: Inline
        spec = AgentSpec(
            id="my-agent",
            name="My Agent",
            instructions="You are a helpful assistant."
        )

        # Mode 2: Dynamic loading
        spec = AgentSpec(
            id="container-pilot",
            name="Container Pilot",
            agent_dir=Path("pilots/container")
        ).load()
    """

    # Identity
    id: str  # Unique identifier
    name: str  # Display name
    version: str = "1.0.0"

    # Dynamic Loading
    agent_dir: Optional[Path] = None  # Folder to load from

    # System Instructions
    instructions: str = ""  # Base system prompt
    instruction_modifiers: list[str] = Field(
        default_factory=list
    )  # Legacy: inline rules

    # Dynamically loaded content
    rules: list[str] = Field(default_factory=list)  # From rules/*.md
    workflows: list[WorkflowConfig] = Field(default_factory=list)  # From workflows/*.md
    knowledge: list[str] = Field(default_factory=list)  # From knowledge/*.md

    # Capabilities
    include_filesystem: bool = False  # File read/write tools
    include_todo: bool = False  # Task decomposition
    include_subagents: bool = False  # Delegation capability

    # Subagents
    subagents: list[SubAgentConfig] = Field(default_factory=list)

    # Skills (Markdown - Job Training)
    skills: list[SkillConfig] = Field(default_factory=list)

    # Tools (Python - The Hands)
    tools: list[str] = Field(default_factory=list)  # List of tool module paths/IDs

    # Tool approval (true = require user confirmation)
    interrupt_on: dict[str, bool] = Field(default_factory=dict)

    # History management
    summarization_config: Optional[SummarizationConfig] = None

    # LLM Configuration
    model: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 4096
    retries: int = 3

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow Path type

    def load(self) -> "AgentSpec":
        """
        Load content from agent_dir if set.

        Reads:
        - instructions.md → self.instructions
        - rules/*.md → self.rules
        - knowledge/*.md → self.knowledge
        - workflows/*.md → self.workflows (with frontmatter parsing)

        Returns self for chaining.
        """
        if not self.agent_dir or not self.agent_dir.exists():
            return self

        # Load instructions.md
        instructions_file = self.agent_dir / "instructions.md"
        if instructions_file.exists():
            self.instructions = instructions_file.read_text(encoding="utf-8")

        # Load rules/*.md
        rules_dir = self.agent_dir / "rules"
        if rules_dir.exists():
            for rule_file in sorted(rules_dir.glob("*.md")):
                self.rules.append(rule_file.read_text(encoding="utf-8"))

        # Load knowledge/*.md
        knowledge_dir = self.agent_dir / "knowledge"
        if knowledge_dir.exists():
            for kb_file in sorted(knowledge_dir.glob("*.md")):
                self.knowledge.append(kb_file.read_text(encoding="utf-8"))

        # Load workflows/*.md (with frontmatter parsing)
        workflows_dir = self.agent_dir / "workflows"
        if workflows_dir.exists():
            for wf_file in sorted(workflows_dir.glob("*.md")):
                content = wf_file.read_text(encoding="utf-8")
                wf = WorkflowConfig(name=wf_file.stem, content=content)
                wf = self._parse_workflow_frontmatter(wf, content)
                self.workflows.append(wf)

        return self

    def _parse_workflow_frontmatter(
        self, wf: WorkflowConfig, content: str
    ) -> WorkflowConfig:
        """Parse YAML frontmatter from workflow file."""
        if not content.startswith("---"):
            return wf

        parts = content.split("---", 2)
        if len(parts) < 3:
            return wf

        for line in parts[1].strip().split("\n"):
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key == "description":
                wf.description = value.strip("\"'")
            elif key == "triggers":
                # Parse: [a, b, c] or "a, b, c"
                if value.startswith("["):
                    triggers = value.strip("[]").split(",")
                    wf.triggers = [t.strip().strip("\"'") for t in triggers]
                else:
                    wf.triggers = [t.strip() for t in value.split(",")]

        return wf

    def get_full_instructions(self) -> str:
        """Compose complete system prompt from all sources."""
        parts = [self.instructions]

        # Legacy inline modifiers (backward compatibility)
        if self.instruction_modifiers:
            parts.append("\n\n## Rules\n")
            parts.extend(f"- {mod}" for mod in self.instruction_modifiers)

        # Dynamically loaded rules
        if self.rules:
            parts.append("\n\n## Behavioral Rules\n")
            parts.extend(self.rules)

        # Dynamically loaded knowledge
        if self.knowledge:
            parts.append("\n\n## Context\n")
            parts.extend(self.knowledge)

        return "\n".join(parts)

    def get_workflow(self, name: str) -> Optional[WorkflowConfig]:
        """Get a workflow by name."""
        for wf in self.workflows:
            if wf.name == name:
                return wf
        return None

    def get_workflow_by_trigger(self, trigger: str) -> Optional[WorkflowConfig]:
        """Find workflow that matches a trigger keyword."""
        trigger_lower = trigger.lower()
        for wf in self.workflows:
            if any(
                t.lower() in trigger_lower or trigger_lower in t.lower()
                for t in wf.triggers
            ):
                return wf
        return None

    def to_dict(self) -> dict[str, Any]:
        """Export as dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "instructions": self.get_full_instructions(),
            "model": self.model,
            "temperature": self.temperature,
            "maxTokens": self.max_tokens,
            "includeFilesystem": self.include_filesystem,
            "includeTodo": self.include_todo,
            "includeSubagents": self.include_subagents,
            "subagents": [
                {
                    "name": sa.name,
                    "description": sa.description,
                    "triggers": sa.triggers,
                }
                for sa in self.subagents
            ],
            "workflows": [
                {
                    "name": wf.name,
                    "description": wf.description,
                    "triggers": wf.triggers,
                }
                for wf in self.workflows
            ],
            "interruptOn": self.interrupt_on,
        }


def load_agent_spec(agent_id: str, base_dir: Optional[Path] = None) -> AgentSpec:
    """
    Factory function to load an agent spec from folder structure.

    Args:
        agent_id: Folder name (e.g., "container", "studio", "workspace")
        base_dir: Directory containing agent folders

    Returns:
        Loaded AgentSpec with all content populated

    Raises:
        ValueError: If agent folder doesn't exist or has no valid spec
    """
    if base_dir is None:
        raise ValueError("base_dir must be provided")

    agent_dir = base_dir / agent_id
    if not agent_dir.exists():
        raise ValueError(f"Agent '{agent_id}' not found at {agent_dir}")

    # Try to import spec from __init__.py
    spec_module = agent_dir / "__init__.py"
    if spec_module.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location(f"agents.{agent_id}", spec_module)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for AGENT_SPEC or PILOT_SPEC
        for attr_name in ["AGENT_SPEC", "PILOT_SPEC"]:
            if hasattr(module, attr_name):
                agent_spec = getattr(module, attr_name).model_copy()
                agent_spec.agent_dir = agent_dir
                return agent_spec.load()

    # Fallback: create minimal spec from folder
    return AgentSpec(
        id=agent_id,
        name=agent_id.replace("-", " ").replace("_", " ").title(),
        agent_dir=agent_dir,
    ).load()
