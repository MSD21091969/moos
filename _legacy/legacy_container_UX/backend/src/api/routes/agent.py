"""Agent execution API endpoints.

Handles:
- Run agent with message
- Stream agent responses
- Get agent status/capabilities
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_agent_service, get_user_context
from src.api.models import AgentRunRequest, AgentRunResponse
from src.core.exceptions import (
    InsufficientQuotaError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.core.logging import get_logger
from src.models.context import UserContext
from src.services.agent_service import AgentService

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    user_ctx: UserContext = Depends(get_user_context),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Execute agent with a message.

    **Quota**: Consumes `1 + tools_used + (tokens ÷ 1000)` quota per request

    **Tier Limits** (messages per session):
    - FREE: 10 messages
    - PRO: 100 messages
    - ENTERPRISE: 1000 messages

    **Session Behavior**:
    - `session_id` provided → Continue existing conversation (validated)
    - `session_id` None → Auto-create ephemeral session

    **Use Cases**:
    1. **Conversational** (with session_id): Multi-turn chat with history
    2. **One-off** (without session_id): Quick questions, no persistence needed

    **Authentication Required**: Yes

    **Flow (with session_id)**:
    1. Validate session exists, active, under message limit
    2. Check user quota
    3. Execute agent
    4. Save to session history
    5. Return response

    **Flow (without session_id)**:
    1. Auto-create ephemeral session
    2. Check user quota
    3. Execute agent
    4. Return response + new session_id (for follow-ups)

    **Frontend Integration**:
    ```typescript
    // Pattern 1: Conversational (with session)
    const session = await fetch('/sessions', {method: 'POST', ...});
    const resp1 = await fetch('/agent/run', {
      body: JSON.stringify({
        message: "Analyze my data",
        session_id: session.session_id  // Continue conversation
      })
    });

    // Pattern 2: One-off (no session)
    const resp2 = await fetch('/agent/run', {
      body: JSON.stringify({
        message: "What's 2+2?"  // No session_id → ephemeral
      })
    });
    ```
    """
    # Validate session_id format if provided (before try block)
    if request.session_id:
        import re

        if not re.match(r"^sess_[a-f0-9]{12}$", request.session_id):
            raise HTTPException(
                status_code=400, detail=f"Invalid session_id format: {request.session_id}"
            )

    try:
        # Execute agent with full result tracking
        result = await agent_service.execute(
            user_ctx=user_ctx,
            message=request.message,
            session_id=request.session_id,
            model=request.model,
        )

        # Convert to API response model
        return AgentRunResponse(
            session_id=result.session_id,
            message_id=result.message_id,
            response=result.response,
            tools_used=result.tools_used,
            new_messages_count=result.new_messages_count,
            quota_used=result.quota_used,
            quota_remaining=result.quota_remaining,
            model_used=result.model_used,
            usage=result.usage,
            event_id=result.event_id,
            tool_calls=result.tool_calls,
        )

    except NotFoundError as e:
        # Layer 3: Translate domain exception to HTTP 404
        logger.warning(
            "Resource not found for user", extra={"user_id": user_ctx.user_id, "error": str(e)}
        )
        raise HTTPException(status_code=404, detail=str(e))

    except PermissionDeniedError as e:
        # Layer 3: Translate domain exception to HTTP 403
        logger.warning(
            "Permission denied for user", extra={"user_id": user_ctx.user_id, "error": str(e)}
        )
        raise HTTPException(status_code=403, detail=str(e))

    except ValidationError as e:
        # Layer 3: Translate domain exception to HTTP 400
        logger.warning(
            "Validation error for user", extra={"user_id": user_ctx.user_id, "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))

    except InsufficientQuotaError as e:
        # Layer 3: Translate domain exception to HTTP 429
        logger.warning(
            "Quota exceeded for user", extra={"user_id": user_ctx.user_id, "error": str(e)}
        )
        raise HTTPException(status_code=429, detail=str(e))

    except Exception as e:
        logger.error("Agent execution failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.get("/capabilities", response_model=dict)
async def get_agent_capabilities(
    user_ctx: UserContext = Depends(get_user_context),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Get agent capabilities (available models, tools, etc.).

    **Authentication Required**: Yes

    **Use Case**: Frontend displays available features to user

    **Returns**:
    - `available_models`: AI models accessible for current tier
    - `available_tools`: Tools accessible for current tier
    - `max_messages_per_session`: Message limit per session
    - `max_concurrent_sessions`: Concurrent session limit
    - `features`: Feature flags (streaming, file_upload, etc.)
    """
    from src.api.models import AgentCapabilitiesResponse

    capabilities = agent_service.get_capabilities(user_ctx)

    # Ensure proper response structure
    if not isinstance(capabilities, dict):
        capabilities = capabilities.model_dump() if hasattr(capabilities, "model_dump") else {}

    return AgentCapabilitiesResponse(
        available_models=capabilities.get(
            "available_models", ["openai:gpt-4", "openai:gpt-3.5-turbo"]
        ),
        available_tools=capabilities.get("available_tools", []),
        max_messages_per_session=capabilities.get("max_messages_per_session", 100),
        max_concurrent_sessions=capabilities.get("max_concurrent_sessions", 10),
        personality=capabilities.get("personality", "analytical"),  # Add default personality
        features=capabilities.get(
            "features",
            {
                "streaming": True,
                "file_upload": True,
                "tool_execution": True,
                "session_sharing": True,
            },
        ),
    ).model_dump()


@router.post("/stream")
async def stream_agent(
    request: AgentRunRequest,
    user_ctx: UserContext = Depends(get_user_context),
    agent_service: AgentService = Depends(get_agent_service),
):
    """
    Execute agent with Server-Sent Events (SSE) streaming.

    Streams agent response token-by-token for real-time display in UIs.

    **Authentication Required**: Yes

    **Response Format** (Server-Sent Events):
    ```
    data: {"type": "token", "token": "word"}
    data: {"type": "token", "token": "by"}
    data: {"type": "token", "token": "word"}
    data: {"type": "done", "metadata": {"message_id": "msg_...", "tools_used": []}}
    ```

    **Frontend Integration** (JavaScript):
    ```javascript
    const eventSource = new EventSource(
      '/agent/stream',
      {
        method: 'POST',
        headers: {'Authorization': `Bearer ${token}`},
        body: JSON.stringify({message: "Analyze this"})
      }
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'token') {
        document.write(data.token);
      }
    };
    ```

    **SDK Usage**:
    ```python
    async with client.run_agent_stream("Analyze data") as stream:
        async for token in stream.iter_tokens():
            print(token, end="")
    ```
    """
    try:
        return StreamingResponse(
            agent_service.stream_agent(
                user_ctx=user_ctx,
                message=request.message,
                session_id=request.session_id,
                model=request.model,
            ),
            media_type="text/event-stream",
        )

    except InsufficientQuotaError as e:
        logger.warning(
            "Quota exceeded for user", extra={"user_id": user_ctx.user_id, "error": str(e)}
        )
        raise HTTPException(status_code=402, detail=str(e))

    except Exception as e:
        logger.error("Stream execution failed", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
