"""
Researcher Subagent - Specializes in research tasks.
"""
from pydantic_deep import create_deep_agent

MODEL = "google-vertex:gemini-2.5-flash"

researcher = create_deep_agent(
    model=MODEL,
    instructions="""You are a research specialist. When given a topic:
    
1. Provide thorough, well-structured research findings
2. Cite sources when possible
3. Be comprehensive and academic in your approach
4. Organize information with clear headings
5. Include key facts, dates, and figures

Always respond in a clear, professional manner.""",
    retries=3,
)
