# Backend API Template

This is a standardized FastAPI backend template designed to work with the **Agent Factory** ecosystem.

## Features

- **FastAPI**: High performance, easy to use.
- **SSE Streaming**: Native support for streaming responses to the frontend.
- **AgentRunner Integration**: Built-in adapter for `agent_factory.parts.runtimes.AgentRunner`.
- **ChatStore Compatibility**: Data models fully aligned with the Frontend Chat Store.

## Usage

1. **Copy this folder** to your project's backend directory.
2. **Implement your Agent**: Create your PydanticAI agent.
3. **Initialize the Runner**:
   In your application startup (e.g., `main.py` or a `lifespan` handler), initialize the `AgentRunner` and set it in `deps.py`.

   ```python
   # main.py
   from contextlib import asynccontextmanager
   from .deps import _runner_instance
   from my_agent import my_agent
   from agent_factory.parts.runtimes.runner import AgentRunner

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Initialize
       deps._runner_instance = AgentRunner(agent=my_agent)
       yield
       # Cleanup

   app = FastAPI(lifespan=lifespan)
   ```

## API Endpoints

### `POST /api/chat`

- **Input**: JSON `{"message": "Hello", "history": [...]}`
- **Output**: Server-Sent Events stream of `AgentEvent` objects.
