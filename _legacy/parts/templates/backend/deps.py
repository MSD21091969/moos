from typing import Optional
from agent_factory.parts.runtimes.runner import AgentRunner
# In a real app, you would import your specific agent here
# from my_agent import agent

_runner_instance: Optional[AgentRunner] = None

def get_agent_runner() -> AgentRunner:
    """
    Dependency to get the active AgentRunner instance.
    In a real application, this would probably be initialized via a lifespan event
    or configuration.
    
    For the template, we'll raise an error if not configured, or return a mock.
    """
    global _runner_instance
    if _runner_instance is None:
        # In a real app, this would be initialized at startup
        raise RuntimeError("AgentRunner has not been initialized. Please set deps._runner_instance in your app startup.")
    return _runner_instance
