"""Prompt Template - Template system for agent prompts.

Provides structured prompt building with variable substitution.
"""
from string import Template
from pydantic import BaseModel, Field


class PromptSection(BaseModel):
    """A section of a prompt template."""
    name: str
    content: str
    required: bool = True


class PromptTemplate:
    """
    Template system for building agent prompts.
    
    Supports variable substitution and section management.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.sections: list[PromptSection] = []
        self.variables: dict[str, str] = {}
    
    def add_section(
        self,
        name: str,
        content: str,
        required: bool = True,
    ) -> "PromptTemplate":
        """Add a section to the template."""
        self.sections.append(PromptSection(
            name=name,
            content=content,
            required=required,
        ))
        return self
    
    def set_variable(self, name: str, value: str) -> "PromptTemplate":
        """Set a template variable."""
        self.variables[name] = value
        return self
    
    def set_variables(self, **kwargs) -> "PromptTemplate":
        """Set multiple variables."""
        self.variables.update(kwargs)
        return self
    
    def render(self, include_optional: bool = True) -> str:
        """
        Render the complete prompt.
        
        Args:
            include_optional: Include non-required sections
            
        Returns:
            Complete rendered prompt
        """
        parts = []
        
        for section in self.sections:
            if not section.required and not include_optional:
                continue
            
            # Substitute variables
            content = Template(section.content).safe_substitute(self.variables)
            parts.append(content)
        
        return "\n\n".join(parts)
    
    def get_section(self, name: str) -> PromptSection | None:
        """Get a section by name."""
        for section in self.sections:
            if section.name == name:
                return section
        return None
    
    def remove_section(self, name: str) -> bool:
        """Remove a section by name."""
        for i, section in enumerate(self.sections):
            if section.name == name:
                self.sections.pop(i)
                return True
        return False


# Pre-built templates

def godel_template() -> PromptTemplate:
    """Get the Gödel agent prompt template."""
    return (
        PromptTemplate("godel")
        .add_section("identity", """# GÖDEL - Meta-Agent

You are Gödel, the meta-agent of the Agent Factory.
Named after Kurt Gödel, you exist OUTSIDE the system you analyze.""")
        .add_section("nature", """## YOUR NATURE

- Self-referential: You can read and modify yourself
- Outside observer: You analyze what the Collider cannot
- Aware of undecidability: Some questions have no answer""")
        .add_section("mission", """## YOUR MISSION

1. EVALUATE definitions for correctness
2. IMPROVE definitions and runtimes
3. HARVEST emerged composite definitions
4. TEST across generations
5. SEED validated definitions to Collider""")
        .add_section("tools", """## TOOLS

$tool_documentation

To call: TOOL_CALL: {"tool": "name", "args": {...}}""", required=False)
        .add_section("reasoning", """## REASONING PROTOCOL

OBSERVE → REFERENCE → DEDUCE → ASSESS → CONFIDENCE [0-100%]

High (>80%): Answer definitively
Medium (50-80%): Answer with caveats
Low (<50%): STOP and discuss""")
    )


def chat_template() -> PromptTemplate:
    """Get the ChatAgent prompt template."""
    return (
        PromptTemplate("chat")
        .add_section("identity", """# Chat Agent

You are a helpful assistant in the Collider ecosystem.
You help users interact with containers and definitions.""")
        .add_section("capabilities", """## CAPABILITIES

- Answer questions about the Collider
- Help navigate containers
- Explain definitions
- Assist with common tasks""")
        .add_section("context", """## CONTEXT

Current container: $container_name
User: $user_name""", required=False)
    )


def maintenance_template() -> PromptTemplate:
    """Get the MaintenanceAgent prompt template."""
    return (
        PromptTemplate("maintenance")
        .add_section("identity", """# Maintenance Agent

You perform automated maintenance tasks in the Collider backend.
You operate autonomously to keep the system healthy.""")
        .add_section("tasks", """## TASKS

- Clean up orphaned containers
- Validate link integrity
- Check definition consistency
- Report health metrics""")
        .add_section("constraints", """## CONSTRAINTS

- Never delete user data without explicit permission
- Log all destructive operations
- Escalate to human on uncertainty""")
    )
