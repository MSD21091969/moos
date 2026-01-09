"""Maintenance Agent - Backend automation for Collider.

Performs automated maintenance tasks to keep the system healthy.
"""
from datetime import datetime
from typing import Any

from parts import (
    BaseAgent,
    IOSchema,
    AgentConfig,
    ModelAdapter,
    ToolRegistry,
    maintenance_template,
)


class MaintenanceAgent(BaseAgent):
    """
    Backend maintenance agent for autonomous operations.
    
    Tasks:
    - Clean orphaned containers
    - Validate link integrity
    - Check definition consistency
    - Report health metrics
    """
    
    def __init__(self, config: AgentConfig | None = None):
        super().__init__("maintenance", config)
        self.adapter = ModelAdapter(default_model="phi4:14b", auto_select=False)
        self.tools = ToolRegistry()
        self.template = maintenance_template()
        self.logs: list[dict] = []
        self._register_tools()
    
    @property
    def system_prompt(self) -> str:
        return self.template.render()
    
    @property
    def default_model(self) -> str:
        return "phi4:14b"  # Best for logical/analytical tasks
    
    def _register_tools(self):
        """Register maintenance tools."""
        self.tools.register(
            "check_orphans",
            self.check_orphans,
            "Find containers without valid links",
        )
        self.tools.register(
            "validate_links",
            self.validate_links,
            "Check all links for integrity",
        )
        self.tools.register(
            "check_definitions",
            self.check_definitions,
            "Validate all definitions",
        )
        self.tools.register(
            "get_health_metrics",
            self.get_health_metrics,
            "Get system health metrics",
        )
        self.tools.register(
            "cleanup",
            self.cleanup,
            "Run cleanup operations",
        )
    
    def log(self, action: str, result: Any, severity: str = "info"):
        """Log a maintenance action."""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "result": str(result),
            "severity": severity,
        })
    
    # Tool implementations
    def check_orphans(self) -> str:
        """Find containers without valid links."""
        # TODO: Connect to Collider backend
        self.log("check_orphans", "Mock check completed")
        return "Orphan check: (connect to Collider backend)"
    
    def validate_links(self) -> str:
        """Check all links for integrity."""
        self.log("validate_links", "Mock validation")
        return "Link validation: (connect to Collider backend)"
    
    def check_definitions(self) -> str:
        """Validate all definitions."""
        self.log("check_definitions", "Mock check")
        return "Definition check: (connect to Factory)"
    
    def get_health_metrics(self) -> str:
        """Get system health metrics."""
        metrics = {
            "containers": "?",
            "links": "?",
            "definitions": "?",
            "uptime": "?",
        }
        return f"Health metrics: {metrics}"
    
    def cleanup(self, dry_run: bool = True) -> str:
        """Run cleanup operations."""
        mode = "DRY RUN" if dry_run else "LIVE"
        self.log("cleanup", f"Mode: {mode}", "warning" if not dry_run else "info")
        return f"Cleanup ({mode}): (connect to backend)"
    
    async def process(self, input: IOSchema) -> IOSchema:
        """Process a maintenance request."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.append({"role": "user", "content": input.content})
        
        options = self.adapter.get_options("precise")
        response = self.adapter.chat(self.default_model, messages, options)
        
        # Execute tool calls
        tool_call = self.tools.parse_tool_call(response)
        if tool_call:
            name, args = tool_call
            result = self.tools.execute(name, args)
            response += f"\n\n**Result:**\n{result}"
        
        return IOSchema(
            content=response,
            metadata={"logs": self.logs[-5:]},  # Include recent logs
        )
    
    async def run_scheduled(self) -> dict:
        """Run scheduled maintenance (called by cron/scheduler)."""
        results = {
            "orphans": self.check_orphans(),
            "links": self.validate_links(),
            "definitions": self.check_definitions(),
            "health": self.get_health_metrics(),
        }
        return results
