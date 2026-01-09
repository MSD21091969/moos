"""Chat Agent - User-facing chat assistant for frontend.

Provides conversational interface for Collider users.
"""
from parts import (
    BaseAgent,
    IOSchema,
    AgentConfig,
    ModelAdapter,
    ToolRegistry,
    chat_template,
)


class ChatAgent(BaseAgent):
    """
    User-facing chat agent for the frontend.
    
    Capabilities:
    - Answer questions about Collider
    - Help navigate containers
    - Explain definitions
    - General assistance
    """
    
    def __init__(
        self,
        user_name: str = "User",
        container_name: str | None = None,
        config: AgentConfig | None = None,
    ):
        super().__init__("chat", config)
        self.user_name = user_name
        self.container_name = container_name
        self.adapter = ModelAdapter(default_model="gemma3:12b", auto_select=False)
        self.tools = ToolRegistry()
        self.template = chat_template()
        self._register_tools()
    
    @property
    def system_prompt(self) -> str:
        self.template.set_variables(
            user_name=self.user_name,
            container_name=self.container_name or "(none)",
        )
        return self.template.render()
    
    @property
    def default_model(self) -> str:
        return "gemma3:12b"  # Vision-capable for image inputs
    
    def _register_tools(self):
        """Register chat tools."""
        self.tools.register(
            "get_container_info",
            self.get_container_info,
            "Get information about a container",
        )
        self.tools.register(
            "list_containers",
            self.list_containers,
            "List available containers",
        )
        self.tools.register(
            "explain_definition",
            self.explain_definition,
            "Explain what a definition does",
        )
    
    # Tool implementations
    def get_container_info(self, container_id: str) -> str:
        """Get information about a container."""
        # TODO: Connect to actual Collider backend
        return f"Container {container_id}: (mock data - connect to Collider)"
    
    def list_containers(self) -> str:
        """List available containers."""
        # TODO: Connect to actual Collider backend
        return "Containers: (mock data - connect to Collider API)"
    
    def explain_definition(self, definition_name: str) -> str:
        """Explain what a definition does."""
        # TODO: Load from Factory definitions
        return f"Definition {definition_name}: (connect to Factory)"
    
    def set_context(self, container_name: str | None = None, user_name: str | None = None):
        """Update the chat context."""
        if container_name:
            self.container_name = container_name
        if user_name:
            self.user_name = user_name
    
    async def process(self, input: IOSchema) -> IOSchema:
        """Process a chat message."""
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.history[-20:]:
            messages.append(msg)
        messages.append({"role": "user", "content": input.content})
        
        # Check for image in metadata
        model = self.default_model
        if input.metadata.get("has_image"):
            model = "gemma3:12b"  # Ensure vision model
        
        options = self.adapter.get_options("creative")
        response = self.adapter.chat(model, messages, options)
        
        # Handle tool calls
        tool_call = self.tools.parse_tool_call(response)
        if tool_call:
            name, args = tool_call
            if name in self.tools:
                result = self.tools.execute(name, args)
                response += f"\n\n{result}"
        
        self.history.append({"role": "user", "content": input.content})
        self.history.append({"role": "assistant", "content": response})
        
        return IOSchema(content=response, metadata={"model": model})
