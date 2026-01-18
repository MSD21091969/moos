# Ollama + Pydantic-AI Working Example

**Based on research from official docs and examples**

## Correct Setup

### Method 1: Environment Variables (Recommended)

```python
import os
from pydantic_ai import Agent

# Set Ollama baseURL
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
os.environ["OPENAI_API_KEY"] = "ollama"  # Any non-empty string

# Create agent - pydantic-ai will use OpenAIChatModel with Ollama
agent = Agent("openai:qwen3:14b")

result = await agent.run("Hello!")
```

### Method 2: Direct Model Instantiation

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

model = OpenAIChatModel(
    model_name="qwen3:14b",
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

agent = Agent(model)
result = await agent.run("Hello!")
```

## Key Points

1. **pydantic-ai** uses `OpenAIChatModel` for Ollama (OpenAI-compatible API)
2. **pydantic-deep** wraps pydantic-ai, same model usage
3. Ollama serves OpenAI-compatible API at `http://localhost:11434/v1`
4. Model name should match `ollama list` output exactly

## Next Step

Test with minimal example first, then add toolsets.
