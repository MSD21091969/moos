"""Base runtime for executing agent definitions."""
import ollama
from definitions import ColliderAgentDefinition


class AgentRuntime:
    """
    Base runtime that executes a ColliderAgentDefinition.
    
    Definition = WHAT the agent is
    Runtime = HOW the agent executes
    """
    
    def __init__(self, definition: ColliderAgentDefinition):
        self.definition = definition
        self.history: list[dict] = []
    
    def chat(self, message: str) -> str:
        """Send a message to the agent."""
        # Build messages
        messages = [
            {"role": "system", "content": self.definition.system_prompt}
        ]
        messages.extend(self.history[-self.definition.reasoning.max_history:])
        messages.append({"role": "user", "content": message})
        
        # Call Ollama
        response = ollama.chat(
            model=self.definition.model.model_name,
            messages=messages,
        )
        
        assistant_msg = response["message"]["content"]
        
        # Update history
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": assistant_msg})
        
        return assistant_msg
    
    def clear_history(self):
        """Clear conversation history."""
        self.history.clear()
