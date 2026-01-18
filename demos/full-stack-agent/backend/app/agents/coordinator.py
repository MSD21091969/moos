from pydantic_deep import create_deep_agent
from pydantic_ai import RunContext

# Define the model to use (Verified in Exp 3)
MODEL_NAME = "google-vertex:gemini-2.5-flash"

# Create the coordinator agent
# We can add subagents here later, similar to Exp 3
coordinator = create_deep_agent(
    model=MODEL_NAME,
    instructions="""
    You are the Coordinator Agent for the Full Stack Demo.
    Your goal is to assist the user by answering questions, writing files, and coordinating tasks.
    
    You have access to a verified Filesystem Backend.
    Use it to write artifacts when requested.
    """,
    retries=3
)

# Example: Simple tool registration (if needed beyond defaults)
# The default `create_deep_agent` comes with pydantic-deep capabilities.
