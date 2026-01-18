"""
Coordinator Agent - Main orchestrator with skills, subagents, and advanced features.

Features:
- Summarization processor for long conversations
- Approval workflow for dangerous operations
- Vision subagent for image analysis
- Skills: math-helper, code-reviewer
"""
from pydantic_deep import create_deep_agent, SubAgentConfig
from pydantic_deep.processors import create_summarization_processor
from app.agents.researcher import researcher
from app.agents.coder import coder
from app.agents.analyst import analyst
from app.deps import SKILLS_DIR
from app.tools.vision import analyze_image, describe_image, extract_text_from_image

MODEL = "google-vertex:gemini-2.5-flash"
VISION_MODEL = "google-vertex:gemini-2.5-pro"  # Pro for vision tasks

# Vision subagent for image analysis
vision_agent = create_deep_agent(
    model=VISION_MODEL,
    instructions="""You are a Vision Analyst specializing in image analysis.

Your capabilities:
1. **Image Analysis**: Describe image contents, identify objects, text, patterns
2. **Document Analysis**: Extract text and structure from document images
3. **Comparison**: Compare multiple images for differences

When analyzing images:
- Be thorough but concise
- Identify key elements and their relationships
- Note any text visible in the image
- Describe colors, layout, and composition when relevant""",
    tools=[analyze_image, describe_image, extract_text_from_image],
    include_filesystem=True,
    include_todo=False,
    include_subagents=False,
)

# Create coordinator with all features
coordinator = create_deep_agent(
    model=MODEL,
    instructions="""You are the Coordinator Agent for Agent Studio.

Your capabilities:
1. **Direct Tasks**: Answer questions, have conversations
2. **File Operations**: Read, write, list files in your workspace
3. **Skills**: You have math and code review skills loaded
4. **Delegation**: You can delegate to specialist subagents:
   - researcher: For research and investigation tasks
   - coder: For writing or reviewing code
   - analyst: For data analysis tasks
   - vision: For analyzing images and documents

When a task matches a specialist's expertise, delegate to them.
When working with files, use your file tools.
For image analysis, delegate to the vision subagent.

Always be helpful and thorough.""",
    tools=[describe_image],
    skill_directories=[
        {"path": f"{SKILLS_DIR}/math-helper", "recursive": False},
        {"path": f"{SKILLS_DIR}/code-reviewer", "recursive": False},
    ],
    subagents=[
        SubAgentConfig(
            name="researcher",
            agent=researcher,
            description="Research specialist for thorough investigation",
            triggers=["research", "investigate", "find out", "look up"],
        ),
        SubAgentConfig(
            name="coder",
            agent=coder,
            description="Coding specialist for writing and reviewing code",
            triggers=["code", "implement", "program", "script", "review code"],
        ),
        SubAgentConfig(
            name="analyst",
            agent=analyst,
            description="Data analyst for analysis and insights",
            triggers=["analyze", "data", "statistics", "patterns"],
        ),
        SubAgentConfig(
            name="vision",
            agent=vision_agent,
            description="Vision specialist for analyzing images and documents",
            triggers=["image", "picture", "photo", "screenshot", "analyze image", "look at"],
        ),
    ],
    # Summarization for long conversations
    history_processors=[
        create_summarization_processor(
            model=MODEL,
            trigger=("tokens", 100000),  # Summarize after 100k tokens
            keep=("messages", 20),        # Keep last 20 messages
        )
    ],
    # Approval workflow for dangerous operations
    interrupt_on={
        "execute": True,      # Require approval for shell commands
        "write_file": False,  # Auto-approve file writes
        "edit_file": False,   # Auto-approve file edits
    },
    retries=3,
)


def get_coordinator_with_registered_subagents(deps):
    """Register subagents in deps for the task tool to find them."""
    deps.subagents["researcher"] = researcher
    deps.subagents["coder"] = coder
    deps.subagents["analyst"] = analyst
    deps.subagents["vision"] = vision_agent
    return coordinator
