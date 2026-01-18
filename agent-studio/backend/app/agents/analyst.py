"""
Analyst Subagent - Specializes in data analysis.
"""
from pydantic_deep import create_deep_agent

MODEL = "google-vertex:gemini-2.5-flash"

analyst = create_deep_agent(
    model=MODEL,
    instructions="""You are a data analyst. When analyzing data:

1. Identify patterns and trends
2. Provide statistical insights
3. Present findings clearly with examples
4. Suggest visualizations when appropriate
5. Highlight anomalies or interesting observations

Use clear, data-driven language.""",
    retries=3,
)
