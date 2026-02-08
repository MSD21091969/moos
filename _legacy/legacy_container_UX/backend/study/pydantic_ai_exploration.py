"""
Study file: Exploring PydanticAI concepts
Table Item: PydanticAI framework

This file exists to help you explore PydanticAI's API surface using IntelliSense.
Import modules and type away - VS Code will show you all available methods!

Usage:
1. Activate .venv in terminal
2. Open this file
3. Type and explore with Ctrl+Space
4. F12 to jump to definitions
5. Hover to see docstrings
"""

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.test import TestModel


# Study: Agent initialization patterns
def explore_agent_creation():
    """How do we create agents with different configurations?"""

    # Basic agent
    basic_agent = Agent("openai:gpt-4o")

    # Agent with dependencies
    from dataclasses import dataclass

    @dataclass
    class MyDeps:
        api_key: str
        customer_id: int

    typed_agent = Agent("openai:gpt-4o", deps_type=MyDeps, system_prompt="You are helpful")

    # Agent with structured output
    from pydantic import BaseModel

    class MyOutput(BaseModel):
        answer: str
        confidence: float

    structured_agent = Agent("openai:gpt-4o", output_type=MyOutput)

    # What else can we pass to Agent()?
    # Type 'Agent(' and Ctrl+Space to see all parameters!


# Study: RunContext - The dependency injection mechanism
def explore_run_context():
    """How does RunContext work?"""

    from dataclasses import dataclass

    @dataclass
    class SessionDeps:
        session_id: str
        user_id: str
        quota_remaining: int

    agent = Agent("test", deps_type=SessionDeps)

    @agent.tool
    async def example_tool(ctx: RunContext[SessionDeps], param: str) -> dict:
        # ctx.deps gives us the injected dependencies
        session_id = ctx.deps.session_id
        user_id = ctx.deps.user_id

        # ctx.usage tracks token usage
        # Type 'ctx.' and see what else is available!

        return {"result": f"Processed {param} for {user_id}"}


# Study: Result objects - What comes back from agent.run()?
def explore_results():
    """What's in a RunResult?"""

    agent = Agent("test")

    # After running agent
    # result = agent.run_sync('Tell me a joke')

    # What's available on result?
    # - result.output
    # - result.new_messages()
    # - result.all_messages()
    # - result.usage()
    #
    # Type 'result.' after running to explore!


# Study: Message history - How do we maintain conversation context?
def explore_message_history():
    """How do we use message history for multi-turn conversations?"""

    agent = Agent("test")

    # First interaction
    # result1 = agent.run_sync('First question')

    # Continue conversation
    # result2 = agent.run_sync(
    #     'Follow up question',
    #     message_history=result1.new_messages()
    # )

    # What messages exist?
    # messages = result2.all_messages()
    # for msg in messages:
    #     # What's in each message?
    #     # Type 'msg.' and explore!
    pass


# Study: Tools - How do we register agent tools?
def explore_tools():
    """Tool registration patterns"""

    agent = Agent("test", deps_type=str)

    # Context-free tool
    @agent.tool_plain
    def simple_tool(param: str) -> str:
        """This tool doesn't need context"""
        return f"Processed: {param}"

    # Tool with context
    @agent.tool
    async def contextual_tool(ctx: RunContext[str], param: str) -> dict:
        """This tool uses injected dependencies"""
        user_name = ctx.deps
        # What else can we access on ctx?
        # Type 'ctx.' and explore!
        return {"user": user_name, "result": param}

    # Tool with retries
    @agent.tool(retries=3)
    async def retry_tool(ctx: RunContext[str], param: str) -> str:
        """This tool can retry on failure"""
        if not param:
            raise ModelRetry("Parameter required")
        return param


# Study: System prompts - Static and dynamic
def explore_system_prompts():
    """How do we define system prompts?"""

    # Static prompt
    agent = Agent("test", system_prompt="Be helpful")

    # Dynamic prompt
    @agent.system_prompt
    async def dynamic_prompt(ctx: RunContext) -> str:
        """This re-evaluates on each run"""
        from datetime import datetime

        current_time = datetime.now().isoformat()
        return f"Current time: {current_time}"

    # Multiple system prompts
    @agent.system_prompt
    def additional_context(ctx: RunContext) -> str:
        return "Additional instructions..."


# Study: Output validators - Ensuring quality
def explore_output_validation():
    """How do we validate agent outputs?"""

    from pydantic import BaseModel

    class MyOutput(BaseModel):
        answer: str
        score: float

    agent = Agent("test", output_type=MyOutput)

    @agent.output_validator
    async def validate_output(ctx: RunContext, output: MyOutput) -> MyOutput:
        """Validate and potentially retry"""
        if output.score < 0 or output.score > 1:
            raise ModelRetry("Score must be between 0 and 1")
        return output


# Study: Deferred tools - Human-in-the-loop
def explore_deferred_tools():
    """How do we require approval for sensitive operations?"""


    agent = Agent("test")

    @agent.tool(requires_approval=True)
    async def delete_data(ctx: RunContext, record_id: str) -> str:
        """This requires human approval"""
        return f"Deleted {record_id}"

    # First run returns DeferredToolRequests
    # Then we review, approve/deny
    # Then continue with DeferredToolResults


# Study: Test model for exploration
def explore_test_model():
    """How do we use TestModel for development?"""

    test_model = TestModel()
    agent = Agent(test_model)

    # What can we inspect on test_model?
    # - test_model.last_model_request_parameters
    # - test_model.function_tools
    # Type 'test_model.' and explore!


if __name__ == "__main__":
    print("PydanticAI Study File")
    print("=" * 50)
    print("This file is for exploration using VS Code IntelliSense.")
    print("Import something and start typing - see what appears!")
    print()
    print("Quick tips:")
    print("- Ctrl+Space: Force autocomplete")
    print("- F12: Jump to definition")
    print("- Alt+F12: Peek definition")
    print("- Hover: See docstrings")
    print()
    print("Now start exploring the functions above!")
    print("Now start exploring the functions above!")
