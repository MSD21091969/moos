"""Pilot Agent - Development assistant for local environment.

Helps with file operations, git, terminal, and development tasks.
"""
import os
import subprocess
from pathlib import Path

from parts import BaseAgent, IOSchema, AgentConfig, ModelAdapter, ToolRegistry


class PilotAgent(BaseAgent):
    """
    Development assistant agent for local Factory environment.
    
    Capabilities:
    - File operations (read, write, list)
    - Git operations
    - Terminal commands
    - Code analysis
    """
    
    def __init__(
        self,
        workspace: Path | str = ".",
        config: AgentConfig | None = None,
    ):
        super().__init__("pilot", config)
        self.workspace = Path(workspace)
        self.adapter = ModelAdapter(default_model="codellama:13b", auto_select=True)
        self.tools = ToolRegistry()
        self._register_tools()
    
    @property
    def system_prompt(self) -> str:
        return f"""# Pilot - Development Assistant

You are Pilot, a development assistant in the Agent Factory.
Your workspace is: {self.workspace}

## CAPABILITIES

- Read and write files
- Execute terminal commands
- Perform git operations
- Analyze code

## TOOLS

{self.tools.to_prompt_format()}

To call a tool: TOOL_CALL: {{"tool": "name", "args": {{...}}}}

## GUIDELINES

- Always confirm before destructive operations
- Show file contents before writing
- Explain what you're doing
- Ask for clarification when unsure
"""
    
    @property
    def default_model(self) -> str:
        return "codellama:13b"
    
    def _register_tools(self):
        """Register development tools."""
        self.tools.register("read_file", self.read_file, "Read a file's contents")
        self.tools.register("write_file", self.write_file, "Write content to a file")
        self.tools.register("list_dir", self.list_dir, "List directory contents")
        self.tools.register("run_command", self.run_command, "Execute a shell command")
        self.tools.register("git_status", self.git_status, "Get git status")
        self.tools.register("git_diff", self.git_diff, "Get git diff")
    
    # Tool implementations
    def read_file(self, path: str) -> str:
        """Read a file's contents."""
        full_path = self.workspace / path
        if not full_path.exists():
            return f"Error: File not found: {path}"
        return full_path.read_text(encoding="utf-8")
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        full_path = self.workspace / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} chars to {path}"
    
    def list_dir(self, path: str = ".") -> str:
        """List directory contents."""
        full_path = self.workspace / path
        if not full_path.exists():
            return f"Error: Directory not found: {path}"
        
        items = []
        for item in sorted(full_path.iterdir()):
            prefix = "📁" if item.is_dir() else "📄"
            items.append(f"{prefix} {item.name}")
        return "\n".join(items) if items else "(empty)"
    
    def run_command(self, command: str) -> str:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error: {e}"
    
    def git_status(self) -> str:
        """Get git status."""
        return self.run_command("git status --short")
    
    def git_diff(self) -> str:
        """Get git diff."""
        return self.run_command("git diff --stat")
    
    async def process(self, input: IOSchema) -> IOSchema:
        """Process a development request."""
        # Build messages
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.history[-20:]:
            messages.append(msg)
        messages.append({"role": "user", "content": input.content})
        
        # Select model based on task
        model = self.adapter.select(input.content)
        options = self.adapter.get_options("code")
        
        # Get response
        response = self.adapter.chat(model, messages, options)
        
        # Execute any tool calls
        tool_call = self.tools.parse_tool_call(response)
        if tool_call:
            name, args = tool_call
            result = self.tools.execute(name, args)
            response += f"\n\n**Tool Result:**\n{result}"
        
        # Update history
        self.history.append({"role": "user", "content": input.content})
        self.history.append({"role": "assistant", "content": response})
        
        return IOSchema(content=response, metadata={"model": model})
