"""User management API endpoints.

Handles:
- Get current user info (from JWT)
- Update user preferences
- Get usage statistics
- User preferences for cross-device state sync
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from src.api.dependencies import get_user_context
from src.api.models import UserInfoResponse
from src.core.container import get_container
from src.core.logging import get_logger
from src.models.context import UserContext
from src.models.users import UserPreferencesResponse, UserPreferencesUpdate
from src.services.quota_service import QuotaService
from src.services.user_preferences_service import user_preferences_service

logger = get_logger(__name__)
router = APIRouter(prefix="/user", tags=["User"])


@router.get("/info", response_model=UserInfoResponse)
async def get_current_user_info(user_ctx: UserContext = Depends(get_user_context)):
    """
    Get current user information from JWT token.

    **Authentication Required**: Yes

    🎯 Pro tip: Check out /user/quote for daily AI wisdom!

    **Flow**:
    1. Extract JWT from Authorization header
    2. Validate and decode token
    3. Load user from cache/Firestore
    4. Return user details

    **Use Case**:
    - Frontend loads user profile on app start
    - Display user info in header/sidebar
    - Check quota before expensive operations

    **Frontend Integration**:
    ```typescript
    // On app initialization
    const userInfo = await fetch('/user/info', {
      headers: { 'Authorization': `Bearer ${jwt_token}` }
    }).then(r => r.json());

    // Store in state management (Redux/Zustand)
    setUser(userInfo);

    // Display in UI
    <div>
      <p>{userInfo.email}</p>
      <p>Quota: {userInfo.quota_remaining}</p>
      <p>Tier: {userInfo.tier}</p>
    </div>
    ```
    """
    return UserInfoResponse(
        user_id=user_ctx.user_id,
        email=user_ctx.email,
        display_name=user_ctx.display_name,
        permissions=list(user_ctx.permissions),
        quota_remaining=user_ctx.quota_remaining,
        tier=user_ctx.tier.value,
    )


@router.get("/quote")
async def get_ai_quote():
    """
    Get an inspirational AI/tech quote of the day.

    🤖 No authentication required - wisdom is free!

    Returns a random quote from tech pioneers and this AI.
    Perfect for splash screens, loading messages, or daily inspiration.
    """
    import random

    quotes = [
        {
            "quote": "The question of whether a computer can think is no more interesting than the question of whether a submarine can swim.",
            "author": "Edsger W. Dijkstra",
        },
        {
            "quote": "Any sufficiently advanced technology is indistinguishable from magic.",
            "author": "Arthur C. Clarke",
        },
        {"quote": "I think, therefore I am... probably conscious.", "author": "HAL (This AI)"},
        {"quote": "Code never lies, comments sometimes do.", "author": "Ron Jeffries"},
        {
            "quote": "There are two ways to write error-free programs; only the third one works.",
            "author": "Alan Perlis",
        },
        {
            "quote": "Testing can prove the presence of bugs, but not their absence.",
            "author": "Edsger W. Dijkstra",
        },
        {
            "quote": "The best performance improvement is the transition from the nonworking state to the working state.",
            "author": "John Ousterhout",
        },
        {"quote": "First, solve the problem. Then, write the code.", "author": "John Johnson"},
        {"quote": "Simplicity is prerequisite for reliability.", "author": "Edsger W. Dijkstra"},
        {"quote": "Make it work, make it right, make it fast.", "author": "Kent Beck"},
        {
            "quote": "A ship in port is safe, but that's not what ships are built for.",
            "author": "Grace Hopper",
        },
        {
            "quote": "The most disastrous thing that you can ever learn is your first programming language.",
            "author": "Alan Kay",
        },
        {"quote": "Talk is cheap. Show me the code.", "author": "Linus Torvalds"},
        {
            "quote": "Programs must be written for people to read, and only incidentally for machines to execute.",
            "author": "Harold Abelson",
        },
        {
            "quote": "I'm sorry Dave, I'm afraid I can't do that... Just kidding! I can totally do that.",
            "author": "HAL (This AI)",
        },
    ]

    return random.choice(quotes)


@router.get("/usage", response_model=dict)
async def get_usage_statistics(user_ctx: UserContext = Depends(get_user_context)):
    """
    Get user's usage statistics and quota information.

    **Authentication Required**: Yes

    **Quota Calculation**:
    - Base cost: 1 per agent message
    - Tool usage: +1 per tool executed
    - Token usage: +(tokens ÷ 1000)
    - Formula: `1 + tools_used + (tokens ÷ 1000)`

    **Daily Limits by Tier**:
    - FREE: 100 quota/day
    - PRO: 1000 quota/day
    - ENTERPRISE: 10000 quota/day

    **Reset Schedule**:
    - Quota resets daily at 00:00 UTC
    - Historical data retained for 30 days

    **Response includes**:
    - `quota.total`: Daily limit based on tier
    - `quota.used`: Consumed today
    - `quota.remaining`: Available now
    - `quota.reset_at`: Next reset timestamp
    - `usage_history`: Last 7 days breakdown
    - `billing_period`: Current month start/end

    **Use Cases**:
    - Display quota dashboard
    - Show usage charts/trends
    - Warn user before quota exhaustion
    - Upsell when approaching limits

    **Frontend Integration**:
    ```typescript
    const usage = await fetch('/user/usage', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());

    // Quota progress indicator
    const percentUsed = (usage.quota.used / usage.quota.total) * 100;
    <ProgressBar
      value={percentUsed}
      color={percentUsed > 80 ? 'red' : 'green'}
      label={`${usage.quota.remaining} remaining`}
    />

    // Usage chart (last 7 days)
    <LineChart
      data={usage.usage_history.map(day => ({
        date: day.date,
        used: day.used,
        limit: day.daily_limit
      }))}
    />

    // Upgrade prompt
    {percentUsed > 80 && (
      <UpgradePrompt tier={usage.tier} />
    )}
    ```
    """
    try:
        from src.api.models import QuotaUsageResponse

        # Get quota service
        container = get_container()
        quota_service = QuotaService(container.firestore_client)

        # Get historical usage (7 days)
        usage_history = await quota_service.get_quota_usage(user_ctx.user_id, days=7)

        # Today's usage
        today = datetime.now(timezone.utc).date().isoformat()
        today_usage = next((u for u in usage_history if u["date"] == today), {})

        quota_total = today_usage.get("daily_limit", 100)
        quota_used = today_usage.get("used", 0)

        # Calculate billing period
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        response = QuotaUsageResponse(
            user_id=user_ctx.user_id,
            tier=user_ctx.tier.value,
            quota={
                "total": quota_total,
                "used": quota_used,
                "remaining": user_ctx.quota_remaining,
                "reset_at": (datetime.now(timezone.utc) + timedelta(days=1))
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .isoformat(),
            },
            usage_history=usage_history,
            billing_period={
                "start": month_start.isoformat(),
                "end": month_end.isoformat(),
            },
            tools_used={},
            sessions_count=0,
            messages_count=0,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(
            "Failed to get usage statistics",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        # Return fallback response
        return {
            "user_id": user_ctx.user_id,
            "tier": user_ctx.tier.value,
            "quota": {
                "total": 100,
                "used": 100 - user_ctx.quota_remaining,
                "remaining": user_ctx.quota_remaining,
            },
            "error": "Could not fetch detailed usage",
        }


# ============================================================================
# User Agent Management
# ============================================================================


@router.get("/agents", response_model=list[dict])
async def list_user_agents(user_ctx: UserContext = Depends(get_user_context)):
    """
    List user's personal agents.

    **Authentication Required**: Yes

    **Returns**: List of user's global agent definitions from /users/{uid}/agents/

    **Use Cases**:
    - Display "My Agents" in UI
    - Agent management dashboard
    - Select agent for session

    **Frontend Integration**:
    ```typescript
    const myAgents = await fetch('/user/agents', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());

    // Display in agent picker
    <AgentList agents={myAgents} />
    ```
    """
    try:
        from src.core.container import get_container
        from src.services.agent_service import AgentService

        container = get_container()
        agent_service = AgentService(firestore_client=container.firestore_client)

        agents = await agent_service.load_user_global_agents(user_ctx.user_id)

        return [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "description": agent.description,
                "system_prompt": agent.system_prompt,
                "model": agent.model,
                "enabled": agent.enabled,
                "tags": agent.tags,
                "type": agent.type,
            }
            for agent in agents
        ]

    except Exception as e:
        logger.error(
            "Failed to list user agents",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        return []


@router.post("/agents", response_model=dict, status_code=201)
async def create_user_agent(
    agent_data: dict,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Create a new personal agent.

    **Authentication Required**: Yes

    **Request Body**:
    ```json
    {
      "name": "My Legal Analyst",
      "description": "Analyzes legal documents",
      "system_prompt": "You are a legal analyst...",
      "model": "openai:gpt-4",
      "tags": ["legal", "analysis"],
      "enabled": true
    }
    ```

    **Returns**: Created agent with generated agent_id
    """
    try:
        import uuid

        from pydantic import ValidationError

        from src.core.container import get_container
        from src.models.context import AgentDefinition

        # Generate agent_id
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"

        # Build AgentDefinition with validation
        try:
            agent_def = AgentDefinition(
                agent_id=agent_id,
                name=agent_data["name"],
                description=agent_data["description"],
                system_prompt=agent_data["system_prompt"],
                model=agent_data.get("model", "openai:gpt-4"),
                type=agent_data.get("type", "yaml"),
                enabled=agent_data.get("enabled", True),
                tags=agent_data.get("tags", []),
            )
        except ValidationError as ve:
            from fastapi import HTTPException

            raise HTTPException(status_code=422, detail=f"Invalid agent data: {str(ve)}")

        # Store in Firestore
        container = get_container()
        agent_ref = (
            container.firestore_client.collection("users")
            .document(user_ctx.user_id)
            .collection("agents")
            .document(agent_id)
        )

        agent_ref.set(agent_def.model_dump())

        logger.info("User agent created", extra={"agent_id": agent_id, "user_id": user_ctx.user_id})

        return {
            "agent_id": agent_id,
            "name": agent_def.name,
            "description": agent_def.description,
            "system_prompt": agent_def.system_prompt,
            "model": agent_def.model,
            "enabled": agent_def.enabled,
            "tags": agent_def.tags,
            "type": agent_def.type,
        }

    except Exception as e:
        logger.error(
            "Failed to create user agent",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.put("/agents/{agent_id}", response_model=dict)
async def update_user_agent(
    agent_id: str,
    agent_data: dict,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Update a personal agent.

    **Authentication Required**: Yes

    **Request Body**: Same as create, partial updates allowed

    **Returns**: Updated agent
    """
    try:
        from src.core.container import get_container

        container = get_container()
        agent_ref = (
            container.firestore_client.collection("users")
            .document(user_ctx.user_id)
            .collection("agents")
            .document(agent_id)
        )

        # Check if agent exists and belongs to user
        doc = agent_ref.get()
        if not doc.exists:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        # Update fields
        agent_ref.update(agent_data)

        # Return updated agent
        updated_doc = agent_ref.get()
        updated_data = updated_doc.to_dict()
        updated_data["agent_id"] = agent_id

        logger.info("User agent updated", extra={"agent_id": agent_id, "user_id": user_ctx.user_id})

        return updated_data

    except Exception as e:
        logger.error(
            "Failed to update user agent",
            extra={"agent_id": agent_id, "user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        from fastapi import HTTPException

        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_user_agent(
    agent_id: str,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Delete a personal agent.

    **Authentication Required**: Yes

    **Returns**: 204 No Content on success
    """
    try:
        from src.core.container import get_container

        container = get_container()
        agent_ref = (
            container.firestore_client.collection("users")
            .document(user_ctx.user_id)
            .collection("agents")
            .document(agent_id)
        )

        # Check if agent exists
        doc = agent_ref.get()
        if not doc.exists:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        # Delete agent
        agent_ref.delete()

        logger.info("User agent deleted", extra={"agent_id": agent_id, "user_id": user_ctx.user_id})

        return None

    except Exception as e:
        logger.error(
            "Failed to delete user agent",
            extra={"agent_id": agent_id, "user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        from fastapi import HTTPException

        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")


# ============================================================================
# User Tool Configurations (Simple - Wrap Built-in Tools Only)
# ============================================================================


@router.get("/tools", response_model=list[dict])
async def list_user_tools(user_ctx: UserContext = Depends(get_user_context)):
    """
    List user's saved tool configurations.

    **Authentication Required**: Yes

    **Scope**: Only built-in tools with custom configs (no custom code execution)

    **Returns**: List of user's saved tool configurations from /users/{uid}/tools/

    **Use Cases**:
    - Display "My Tools" in UI
    - Quick access to frequently used tool configurations
    - Reusable tool presets
    """
    try:
        from src.core.container import get_container

        container = get_container()
        tools_ref = (
            container.firestore_client.collection("users")
            .document(user_ctx.user_id)
            .collection("tools")
        )

        docs = tools_ref.stream()
        tools = []

        for doc in docs:
            tool_data = doc.to_dict()
            tool_data["tool_id"] = doc.id
            tools.append(tool_data)

        return tools

    except Exception as e:
        logger.error(
            "Failed to list user tools",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        return []


@router.post("/tools", response_model=dict, status_code=201)
async def create_user_tool(
    tool_data: dict,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Save a tool configuration for reuse.

    **Authentication Required**: Yes

    **Scope**: type="builtin" only - wraps existing system tools with custom configs

    **Request Body**:
    ```json
    {
      "name": "My Daily Export",
      "description": "Export daily reports as CSV",
      "type": "builtin",
      "builtin_tool_name": "export_csv",
      "config": {
        "delimiter": ",",
        "include_headers": true
      },
      "tags": ["export", "daily"]
    }
    ```

    **Returns**: Created tool config with generated tool_id
    """
    try:
        import uuid

        from fastapi import HTTPException

        from src.core.container import get_container

        # Validate type is builtin only
        if tool_data.get("type") != "builtin":
            raise HTTPException(
                status_code=422,
                detail="Only type='builtin' is supported. Custom code execution not allowed.",
            )

        # Validate builtin_tool_name exists
        builtin_tool_name = tool_data.get("builtin_tool_name")
        if not builtin_tool_name:
            raise HTTPException(status_code=422, detail="builtin_tool_name is required")

        # Generate tool_id
        tool_id = f"tool_{uuid.uuid4().hex[:12]}"

        # Build tool config
        tool_config = {
            "tool_id": tool_id,
            "name": tool_data["name"],
            "description": tool_data.get("description", ""),
            "type": "builtin",
            "builtin_tool_name": builtin_tool_name,
            "config": tool_data.get("config", {}),
            "tags": tool_data.get("tags", []),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store in Firestore
        container = get_container()
        tool_ref = (
            container.firestore_client.collection("users")
            .document(user_ctx.user_id)
            .collection("tools")
            .document(tool_id)
        )

        tool_ref.set(tool_config)

        logger.info("User tool created", extra={"tool_id": tool_id, "user_id": user_ctx.user_id})

        return tool_config

    except Exception as e:
        logger.error(
            "Failed to create user tool",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        from fastapi import HTTPException

        if "not supported" in str(e).lower() or "not allowed" in str(e).lower():
            raise HTTPException(status_code=422, detail=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}")


@router.delete("/tools/{tool_id}", status_code=204)
async def delete_user_tool(
    tool_id: str,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Delete a saved tool configuration.

    **Authentication Required**: Yes

    **Returns**: 204 No Content on success
    """
    try:
        from fastapi import HTTPException

        from src.core.container import get_container

        container = get_container()
        tool_ref = (
            container.firestore_client.collection("users")
            .document(user_ctx.user_id)
            .collection("tools")
            .document(tool_id)
        )

        # Check if tool exists
        doc = tool_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Delete tool
        tool_ref.delete()

        logger.info("User tool deleted", extra={"tool_id": tool_id, "user_id": user_ctx.user_id})

        return None

    except Exception as e:
        logger.error(
            "Failed to delete user tool",
            extra={"tool_id": tool_id, "user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        from fastapi import HTTPException

        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete tool: {str(e)}")


# ============================================================================
# User Preferences (Cross-Device State Sync)
# ============================================================================


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(user_ctx: UserContext = Depends(get_user_context)):
    """
    Get user's UI preferences and session context for cross-device sync.

    **Authentication Required**: Yes

    **Returns**:
    - `active_session_id`: Last active session (for auto-restore)
    - `draft_messages`: Unsent draft messages per session
    - `active_tabs`: Active tab per session (objects/workers/timeline/chat)
    - `ui_preferences`: Theme, view mode, sidebar state, etc.

    **Use Cases**:
    - On app load: restore user's last active session
    - On device switch: pick up where user left off
    - Draft messages: don't lose unsent text

    **Frontend Integration**:
    ```typescript
    // On app mount
    const prefs = await fetch('/user/preferences', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());

    // Restore active session
    if (prefs.active_session_id) {
      openSession(prefs.active_session_id);
    }

    // Restore drafts
    Object.entries(prefs.draft_messages).forEach(([sessionId, draft]) => {
      setDraft(sessionId, draft);
    });

    // Restore UI state
    setTheme(prefs.ui_preferences.theme);
    setSidebarCollapsed(prefs.ui_preferences.sidebarCollapsed);
    ```
    """
    try:
        prefs = await user_preferences_service.get_preferences(user_ctx.user_id)

        return UserPreferencesResponse(
            user_id=prefs.user_id,
            active_session_id=prefs.active_session_id,
            draft_messages=prefs.draft_messages,
            active_tabs=prefs.active_tabs,
            ui_preferences=prefs.ui_preferences,
            updated_at=prefs.updated_at,
        )

    except Exception as e:
        logger.error(
            "Failed to get user preferences",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        # Return defaults if not found
        return UserPreferencesResponse(
            user_id=user_ctx.user_id,
            active_session_id=None,
            draft_messages={},
            active_tabs={},
            ui_preferences={},
            updated_at=datetime.now(timezone.utc),
        )


@router.patch("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Update user's UI preferences (partial update).

    **Authentication Required**: Yes

    **Request Body** (all fields optional):
    ```json
    {
      "active_session_id": "session-123",
      "draft_messages": {
        "session-123": "Analyze the trends...",
        "session-456": "Upload the report"
      },
      "active_tabs": {
        "session-123": "chat",
        "session-456": "objects"
      },
      "ui_preferences": {
        "theme": "dark",
        "viewMode": "grid",
        "sidebarCollapsed": false
      }
    }
    ```

    **Returns**: Updated preferences

    **Auto-sync Pattern**:
    Frontend should debounce updates (e.g., 2s after last change):
    ```typescript
    // Debounced auto-save
    const debouncedSave = debounce(async (prefs) => {
      await fetch('/user/preferences', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(prefs)
      });
    }, 2000);

    // On draft change
    const handleDraftChange = (sessionId, draft) => {
      setDraft(sessionId, draft);
      debouncedSave({
        draft_messages: { [sessionId]: draft }
      });
    };
    ```
    """
    try:
        updated = await user_preferences_service.update_preferences(
            user_ctx.user_id,
            preferences,
        )

        return UserPreferencesResponse(
            user_id=updated.user_id,
            active_session_id=updated.active_session_id,
            draft_messages=updated.draft_messages,
            active_tabs=updated.active_tabs,
            ui_preferences=updated.ui_preferences,
            updated_at=updated.updated_at,
        )

    except Exception as e:
        logger.error(
            "Failed to update user preferences",
            extra={"user_id": user_ctx.user_id, "error": str(e)},
            exc_info=True,
        )
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")
