"""Demo agent with SessionContext integration and data analysis tools."""

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from src.models.context import SessionContext
from src.core.agent_registry import get_agent_registry

# Define agent with SessionContext as dependency type
# Using TestModel for testing (no API calls)
# For production, switch to: Agent("openai:gpt-4", deps_type=SessionContext)
demo_agent = Agent(
    TestModel(),
    deps_type=SessionContext,
    system_prompt=(
        "You are a helpful data analysis assistant. "
        "You help users analyze data and generate insights. "
        "You have access to tools for checking quotas, permissions, and session information. "
        "Always be clear and concise in your responses."
    ),
)

# Register agent in global registry
agent_registry = get_agent_registry()
agent_registry.register(
    agent_id="demo_agent",
    name="Demo Agent",
    description="Helpful data analysis assistant with quota and permission checking tools",
    agent_instance=demo_agent,
    required_tier="FREE",
    quota_cost_multiplier=1.0,
    tags=["data_analysis", "demo", "helper"],
    default_model="test",
    system_prompt=demo_agent.system_prompt,
)


# Register tools with agent
@demo_agent.tool
async def check_quota(ctx: RunContext[SessionContext]) -> dict:
    """Check remaining quota for the current session."""
    return {
        "user_id": ctx.deps.user_id,
        "quota_remaining": ctx.deps.quota_remaining,
        "permissions": list(ctx.deps.permissions),
        "tier": ctx.deps.tier,
    }


@demo_agent.tool
async def check_permissions(ctx: RunContext[SessionContext], permission: str) -> bool:
    """Check if user has a specific permission."""
    return permission in ctx.deps.permissions


@demo_agent.tool
async def get_session_info(ctx: RunContext[SessionContext]) -> dict:
    """Get information about the current session."""
    return {
        "session_id": ctx.deps.session_id,
        "user_id": ctx.deps.user_id,
        "user_email": ctx.deps.user_email,
        "permissions": list(ctx.deps.permissions),
        "quota_remaining": ctx.deps.quota_remaining,
        "tier": ctx.deps.tier,
    }


@demo_agent.tool
async def calculate_expression(ctx: RunContext[SessionContext], expression: str) -> str:
    """
    Perform a mathematical calculation safely.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5")

    Returns:
        Result of the calculation or error message
    """
    try:
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow}
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # nosec B307
        return str(float(result))
    except Exception as e:
        return f"Error: Invalid expression - {str(e)}"
