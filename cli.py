"""Agent Factory CLI - spawn and manage Collider agents."""
import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from definitions.godel import get_godel
from definitions.base import ColliderAgentDefinition
from runtimes import AgentRuntime
from tools import (
    read_definition,
    list_definitions,
    eval_definition,
    improve_definition,
    read_self,
    modify_self,
    benchmark_runtime,
    improve_runtime,
    export_to_collider,
)


# Tool registry for Gödel
GODEL_TOOLS = {
    "read_definition": read_definition,
    "list_definitions": list_definitions,
    "eval_definition": eval_definition,
    "improve_definition": improve_definition,
    "read_self": read_self,
    "modify_self": modify_self,
    "benchmark_runtime": benchmark_runtime,
    "improve_runtime": improve_runtime,
    "export_to_collider": export_to_collider,
}


class GodelRuntime(AgentRuntime):
    """Extended runtime for Gödel with advanced features."""
    
    def __init__(self, use_custom_model: bool = True, streaming: bool = False):
        super().__init__(get_godel())
        self.tools = GODEL_TOOLS
        self.use_custom_model = use_custom_model
        self.streaming = streaming
        
        # Import options
        from runtimes.options import get_preset
        from runtimes.model_selector import select_model, detect_task_type
        
        self.get_preset = get_preset
        self.select_model = select_model
        self.detect_task_type = detect_task_type
    
    def chat(self, message: str, stream_callback=None) -> str:
        """Chat with model switching, streaming, and tool execution."""
        import ollama
        import json
        import re
        from runtimes.streaming import print_callback
        
        # Detect task type and select model
        task_type = self.detect_task_type(message)
        
        # Use custom godel model or select based on task
        if self.use_custom_model:
            model = "godel"  # Custom Ollama model with embedded prompt
        else:
            model = self.select_model(message, task_type)
        
        # Get options preset based on task
        preset_name = task_type.value if task_type else "reasoning"
        options = self.get_preset(preset_name).to_ollama_dict()
        
        # Build messages
        messages = []
        if not self.use_custom_model:
            # Only add system prompt if not using custom model (it's embedded)
            messages.append({"role": "system", "content": self.definition.system_prompt})
        messages.extend(self.history[-self.definition.reasoning.max_history:])
        messages.append({"role": "user", "content": message})
        
        # Stream or regular response
        if self.streaming:
            from runtimes.streaming import stream_chat
            callback = stream_callback or print_callback
            assistant_msg = stream_chat(model, messages, options, callback)
        else:
            response = ollama.chat(
                model=model,
                messages=messages,
                options=options,
            )
            assistant_msg = response["message"]["content"]
        
        # Check for tool calls
        assistant_msg = self._execute_tool_calls(assistant_msg)
        
        # Update history
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": assistant_msg})
        
        return assistant_msg
    
    def _execute_tool_calls(self, response: str) -> str:
        """Execute any tool calls in the response."""
        import json
        import re
        
        tool_patterns = [
            r'TOOL_CALL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
            r'\*\*TOOL_CALL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})\*\*',
            r'`TOOL_CALL:\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})`',
        ]
        
        for pattern in tool_patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    json_str = match.group(1).replace("'", '"')
                    call = json.loads(json_str)
                    tool_name = call.get("tool")
                    args = call.get("args", {})
                    
                    if tool_name in self.tools:
                        result = self.tools[tool_name](**args)
                        response += f"\n\n**Tool Result:**\n{result}"
                        break
                except json.JSONDecodeError as e:
                    response += f"\n\n⚠️ Tool parse error: {e}"
                except Exception as e:
                    response += f"\n\n⚠️ Tool execution error: {e}"
        
        return response


def spawn_godel(query: str | None = None):
    """Spawn an interactive Gödel session or run single query."""
    print("🔮 Spawning Gödel - the meta-agent...")
    print("=" * 50)
    
    runtime = GodelRuntime()
    
    print(f"Model: {runtime.definition.model.model_name}")
    print(f"Tools: {len(runtime.tools)}")
    
    # Single query mode
    if query:
        print(f"\nQuery: {query}")
        print("-" * 50)
        response = runtime.chat(query)
        print(f"\n{response}")
        return
    
    print("Type 'quit' to exit, 'help' for commands")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n[gödel]> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            
            if user_input.lower() == "help":
                print("\nGödel Commands:")
                print("  quit          - Exit")
                print("  list defs     - List definitions")
                print("  eval <file>   - Evaluate definition")
                print("  read self     - Read own definition")
                print("  benchmark     - Run performance test")
                continue
            
            print("\nThinking...")
            response = runtime.chat(user_input)
            print(f"\n{response}")
            
        except EOFError:
            print("\nEnding session.")
            break
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'quit' to exit.")
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Agent Factory CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # spawn command
    spawn_parser = subparsers.add_parser("spawn", help="Spawn an agent")
    spawn_parser.add_argument("agent", nargs="?", default="godel", help="Agent to spawn")
    spawn_parser.add_argument("-q", "--query", help="Single query (non-interactive)")
    
    # eval command
    eval_parser = subparsers.add_parser("eval", help="Evaluate a definition")
    eval_parser.add_argument("path", help="Path to definition file")
    
    # list command
    subparsers.add_parser("list", help="List available definitions")
    
    # seed command
    seed_parser = subparsers.add_parser("seed", help="Export to Collider")
    seed_parser.add_argument("path", help="Definition to export")
    seed_parser.add_argument("--to", default="D:/my-tiny-data-collider", help="Collider path")
    
    args = parser.parse_args()
    
    if args.command == "spawn":
        if args.agent == "godel":
            spawn_godel(query=args.query)
        else:
            print(f"Unknown agent: {args.agent}")
    
    elif args.command == "eval":
        print(eval_definition(args.path))
    
    elif args.command == "list":
        print(list_definitions())
    
    elif args.command == "seed":
        print(export_to_collider(args.path, args.to))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
