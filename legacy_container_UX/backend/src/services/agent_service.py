"""Agent execution service with business logic."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import logfire

from src.agents.demo_agent import demo_agent
from src.core.exceptions import InsufficientQuotaError, ValidationError
from src.core.logging import get_logger
from src.models.context import AgentDefinition, SessionContext, UserContext
from src.models.permissions import Tier

if TYPE_CHECKING:
    from src.models.agent import AgentInfo

logger = get_logger(__name__)


class AgentExecutionResult:
    """Result from agent execution."""

    def __init__(
        self,
        session_id: str,
        message_id: str,
        response: str,
        tools_used: List[str],
        new_messages_count: int,
        quota_used: int,
        quota_remaining: int,
        model_used: str,
        usage: Dict[str, int],
        event_id: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ):
        self.session_id = session_id
        self.message_id = message_id
        self.response = response
        self.tools_used = tools_used
        self.new_messages_count = new_messages_count
        self.quota_used = quota_used
        self.quota_remaining = quota_remaining
        self.model_used = model_used
        self.usage = usage
        self.event_id = event_id
        self.tool_calls = tool_calls or []


class AgentService:
    """Service for agent execution with business logic.

    Responsibilities:
    - Quota validation (Level 2)
    - Session context creation
    - Agent execution orchestration
    - Usage tracking
    - Tool usage extraction
    - Agent discovery (system + user-global + session-local)
    """

    def __init__(self, session_service=None, tool_service=None, firestore_client=None):
        """Initialize agent service."""
        self.session_service = session_service
        self.tool_service = tool_service
        self.firestore = firestore_client

    async def run_agent(
        self,
        user_ctx: UserContext,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """
        Execute agent and return response text.

        Args:
            user_ctx: User context
            message: User message
            session_id: Optional session ID (auto-creates if None)
            model: Optional model override

        Returns:
            Response text

        Raises:
            InsufficientQuotaError, NotFoundError, PermissionDeniedError, ValidationError
        """
        result = await self.execute(user_ctx, message, session_id, model)
        return result.response

    async def execute(
        self,
        user_ctx: UserContext,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AgentExecutionResult:
        """
        Execute agent with business logic validation.

        Args:
            user_ctx: User context with permissions and quota
            message: User message to process
            session_id: Optional session ID to continue conversation
            model: Optional model override

        Returns:
            AgentExecutionResult with response and metadata

        Raises:
            InsufficientQuotaError: If user has insufficient quota
            NotFoundError: If session_id provided but doesn't exist
            PermissionDeniedError: If session belongs to different user
            ValidationError: If session is inactive or message limit reached
        """
        # Business Rule 1: Quota validation
        if user_ctx.quota_remaining < 1:
            raise InsufficientQuotaError(
                f"User {user_ctx.user_id} has insufficient quota (remaining: {user_ctx.quota_remaining})"
            )

        with logfire.span("agent_execution", user_id=user_ctx.user_id, session_id=session_id):
            # Business Rule 2: Session validation (if provided)
            if session_id:
                from src.core.container import get_container
                from src.models.permissions import get_message_limit
                from src.services.session_service import SessionService

                container = get_container()
                session_service = SessionService(container.firestore_client)

                with logfire.span("validate_session"):
                    # Validate session exists and user owns it (raises NotFoundError or PermissionDeniedError)
                    session = await session_service.get(session_id, user_ctx.user_id)

                    # Business Rule 3: Session must be active
                    if not session.is_active:
                        raise ValidationError(
                            f"Session {session_id} is not active (status: {session.status})"
                        )

                    # Business Rule 4: Tier-based message limit
                    max_messages = get_message_limit(user_ctx.tier)
                    if session.event_count >= max_messages:
                        raise ValidationError(
                            f"Session message limit reached ({session.event_count}/{max_messages}). "
                            f"Create a new session or upgrade tier."
                        )

                    actual_session_id = session_id
                    logger.info(
                        f"Using existing session {session_id} (messages: {session.event_count}/{max_messages})"
                    )
            else:
                # Create new session ID
                actual_session_id = f"sess_{uuid.uuid4().hex[:12]}"
                logger.info("Creating new session", extra={"session_id": actual_session_id})

            # Generate message ID
            message_id = f"msg_{uuid.uuid4().hex[:12]}"

            # Create session context for agent
            session_ctx = SessionContext.from_user_context(
                session_id=actual_session_id, user_ctx=user_ctx
            )

            # Create root event for agent execution
            event_id = None
            try:
                from src.core.container import get_container
                from src.models.events import EventSource, EventStatus, EventType
                from src.services.event_service import EventService

                # Get firestore client from container
                container = get_container()
                event_service = EventService(container.firestore_client)

                # Create PENDING event
                event = await event_service.create_event(
                    session_id=actual_session_id,
                    event_type=EventType.AGENT_INVOKED,
                    source=EventSource.USER,
                    data={
                        "message": message,
                        "user_id": user_ctx.user_id,
                        "model": model or "demo_agent",
                    },
                    parent_event_id=None,
                    status=EventStatus.PENDING,
                )
                event_id = event.event_id

                # Update to IN_PROGRESS
                await event_service.update_event_status(
                    session_id=actual_session_id,
                    event_id=event_id,
                    status=EventStatus.IN_PROGRESS,
                )
            except Exception as e:
                logger.warning("Failed to create event", extra={"error": str(e)})

            # Store user message as USER_MESSAGE event
            if event_id:
                try:
                    with logfire.span("store_user_message"):
                        await event_service.create_event(
                            session_id=actual_session_id,
                            event_type=EventType.USER_MESSAGE,
                            source=EventSource.USER,
                            data={"content": message},
                            parent_event_id=None,  # Root event
                            status=EventStatus.COMPLETED,
                            metadata={"user_id": user_ctx.user_id},
                        )
                except Exception as e:
                    logger.warning("Failed to store user message event", extra={"error": str(e)})

            # Execute agent
            with logfire.span("agent_run", message_length=len(message)):
                result = await demo_agent.run(message, deps=session_ctx)

            # Extract response (handle both str and ModelResponse)
            response_text = str(result.response) if hasattr(result, "response") else str(result)

            # Extract usage stats
            usage = self._extract_usage(result)

            # Extract tools used from messages
            tools_used = self._extract_tools_used(result)

            # Calculate quota consumed
            # Simple formula: 1 base + 1 per tool call + token costs
            quota_used = 1 + len(tools_used)
            if usage.get("total_tokens", 0) > 1000:
                quota_used += usage["total_tokens"] // 1000  # 1 quota per 1k tokens

            new_quota = max(0, user_ctx.quota_remaining - quota_used)

            # Store assistant response as AGENT_MESSAGE event (child of AGENT_RUN_START)
            if event_id:
                try:
                    with logfire.span("store_assistant_response"):
                        await event_service.create_event(
                            session_id=actual_session_id,
                            event_type=EventType.AGENT_MESSAGE,
                            source=EventSource.AGENT,
                            data={
                                "content": response_text,
                                "model": model or "demo_agent",
                                "usage": usage,
                                "tools_used": tools_used,
                            },
                            parent_event_id=event_id,  # Link to AGENT_INVOKED event
                            status=EventStatus.COMPLETED,
                            metadata={"quota_cost": quota_used},
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to store assistant message event", extra={"error": str(e)}
                    )

            # Complete event tracking
            if event_id:
                try:
                    # Update event to COMPLETED
                    await event_service.update_event_status(
                        session_id=actual_session_id,
                        event_id=event_id,
                        status=EventStatus.COMPLETED,
                        result={
                            "response": response_text,
                            "tools_used": tools_used,
                            "quota_used": quota_used,
                        },
                    )
                except Exception as e:
                    logger.warning("Failed to complete event tracking", extra={"error": str(e)})

            # Update user quota (would integrate with quota_service in production)
            # For now, just log
            logfire.info(
                "Agent execution complete",
                response_length=len(response_text),
                tools_used=len(tools_used),
                quota_used=quota_used,
                session_id=actual_session_id,
                event_id=event_id,
            )

            return AgentExecutionResult(
                session_id=actual_session_id,
                message_id=message_id,
                response=response_text,
                tools_used=tools_used,
                new_messages_count=len(result.new_messages()),
                quota_used=quota_used,
                quota_remaining=new_quota,
                model_used=model or "test-model",
                usage=usage,
                event_id=event_id,
            )

    def _extract_usage(self, result: Any) -> Dict[str, int]:
        """Extract token usage from result."""
        usage = {}
        if hasattr(result, "usage") and result.usage:
            usage = {
                "input_tokens": getattr(result.usage, "input_tokens", 0),
                "output_tokens": getattr(result.usage, "output_tokens", 0),
                "total_tokens": (
                    getattr(result.usage, "input_tokens", 0)
                    + getattr(result.usage, "output_tokens", 0)
                ),
            }
        return usage

    def _extract_tools_used(self, result: Any) -> List[str]:
        """Extract tool names from new messages."""
        tools_used = []
        if hasattr(result, "new_messages"):
            for msg in result.new_messages():
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        if hasattr(part, "tool_name"):
                            tools_used.append(part.tool_name)
        return tools_used

    def get_capabilities(self, user_ctx: UserContext) -> Dict[str, Any]:
        """
        Get agent capabilities based on user permissions.

        Args:
            user_ctx: User context with tier and permissions

        Returns:
            Dictionary of available capabilities
        """
        # Base capabilities
        models: List[str] = ["test-model"]
        features: Dict[str, bool] = {
            "streaming": False,
            "function_calling": True,
            "vision": False,
            "file_upload": False,
        }

        # Tier-based enhancements
        tier_value = user_ctx.tier.value
        if tier_value in {"pro", "enterprise"}:
            models.extend(["gpt-4", "claude-3"])
            features["streaming"] = True

        if tier_value == "enterprise":
            features["vision"] = True
            features["file_upload"] = True

        return {"models": models, "features": features}

    async def stream_agent(
        self,
        user_ctx: UserContext,
        message: str,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Execute agent with streaming response (token-by-token).

        For now, this returns a mock stream. In production, would use
        an LLM that supports streaming (e.g., OpenAI streaming API).

        Args:
            user_ctx: User context with permissions and quota
            message: User message to process
            session_id: Optional session ID
            model: Optional model override

        Yields:
            JSON events with format:
            {"type": "token", "token": "word"} or
            {"type": "done", "metadata": {...}}

        Raises:
            InsufficientQuotaError: If insufficient quota
        """
        # Quota validation
        if user_ctx.quota_remaining < 1:
            raise InsufficientQuotaError(f"User {user_ctx.user_id} has insufficient quota")

        # For now, execute normally and stream the response word by word
        result = await self.execute(user_ctx, message, session_id, model)

        # Stream response word by word
        import json

        words = result.response.split()
        for word in words:
            yield f"data: {json.dumps({'type': 'token', 'token': word + ' '})}\n\n"

        # Send completion event
        done_event = {
            "type": "done",
            "metadata": {"message_id": result.message_id, "tools_used": result.tools_used},
        }
        yield f"data: {json.dumps(done_event)}\n\n"

    async def list_agents(self, tier: Tier) -> List["AgentInfo"]:
        """
        List available agents for user tier.

        Args:
            tier: User subscription tier

        Returns:
            List of AgentInfo with agent metadata

        Note:
            Currently only demo_agent is available.
            In production, would query agent registry.
        """
        from src.models.agent import AgentInfo

        # Define available agents
        agents = [
            AgentInfo(
                agent_id="demo_agent",
                name="Demo Agent",
                description="General-purpose conversational agent with tool calling",
                required_tier="free",
                capabilities={
                    "streaming": tier.value in {"pro", "enterprise"},
                    "function_calling": True,
                    "vision": tier.value == "enterprise",
                },
                available_models=["gpt-4o-mini", "gpt-4o"]
                if tier.value != "free"
                else ["gpt-4o-mini"],
                quota_cost_per_message=1,
                enabled=True,
            )
        ]

        # Filter by tier access
        accessible_agents = [
            agent for agent in agents if self._tier_can_access(tier, agent.required_tier)
        ]

        return accessible_agents

    async def get_agent_details(self, agent_id: str) -> "AgentInfo":
        """
        Get detailed information about specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentInfo with full agent details

        Raises:
            NotFoundError: Agent not found
        """
        from src.core.exceptions import NotFoundError
        from src.models.agent import AgentInfo

        # For now, only demo_agent exists
        if agent_id != "demo_agent":
            raise NotFoundError(f"Agent '{agent_id}' not found")

        return AgentInfo(
            agent_id="demo_agent",
            name="Demo Agent",
            description="General-purpose conversational agent with tool calling capabilities",
            required_tier="free",
            capabilities={
                "streaming": True,
                "function_calling": True,
                "vision": False,
                "file_upload": False,
            },
            available_models=["gpt-4o-mini", "gpt-4o"],
            quota_cost_per_message=1,
            enabled=True,
            system_prompt="You are a helpful AI assistant with access to various tools.",
            max_tokens=4096,
            temperature=0.7,
        )

    def _tier_can_access(self, user_tier: Tier | str, required_tier: str) -> bool:
        """Check if user tier can access feature requiring specific tier."""
        tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}

        user_level = tier_hierarchy.get(
            user_tier.value if isinstance(user_tier, Tier) else str(user_tier).lower(), 0
        )
        required_level = tier_hierarchy.get(required_tier.lower(), 0)

        return user_level >= required_level

    async def load_user_global_agents(self, user_id: str) -> List["AgentDefinition"]:
        """
        Load user's global agents from Firestore, including their resources.

        Args:
            user_id: User identifier

        Returns:
            List of user's global agent definitions

        Note:
            Queries /users/{uid}/agents/ collection and /resources subcollection
        """
        if not self.firestore:
            return []

        try:
            from src.models.context import AgentDefinition
            from src.models.links import ResourceLink

            agents_ref = self.firestore.collection("users").document(user_id).collection("agents")
            docs = agents_ref.stream()

            agents: List[AgentDefinition] = []
            for doc in docs:
                agent_data = doc.to_dict()
                agent_data["agent_id"] = doc.id
                
                # Fetch resources subcollection
                resources_ref = agents_ref.document(doc.id).collection("resources")
                resource_docs = resources_ref.stream()
                
                links = []
                async for r_doc in resource_docs:
                    try:
                        links.append(ResourceLink(**r_doc.to_dict()))
                    except Exception as e:
                        logger.warning(f"Skipping invalid resource link in agent {doc.id}: {e}")
                
                agent_data["resource_links"] = links
                agents.append(AgentDefinition(**agent_data))

            logger.info(
                "Loaded user global agents", extra={"user_id": user_id, "count": len(agents)}
            )
            return agents
        except Exception as e:
            logger.warning(
                "Failed to load user global agents", extra={"user_id": user_id, "error": str(e)}
            )
            return []

    async def load_session_local_agents(
        self, user_id: str, session_id: str
    ) -> List["AgentDefinition"]:
        """
        Load session-local agents from Firestore, including their resources.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            List of session-local agent definitions

        Note:
            Queries /users/{uid}/sessions/{sid}/agents/ collection and /resources subcollection
        """
        if not self.firestore:
            return []

        try:
            from src.models.context import AgentDefinition
            from src.models.links import ResourceLink

            agents_ref = (
                self.firestore.collection("users")
                .document(user_id)
                .collection("sessions")
                .document(session_id)
                .collection("agents")
            )
            docs = agents_ref.stream()

            agents: List[AgentDefinition] = []
            for doc in docs:
                agent_data = doc.to_dict()
                agent_data["agent_id"] = doc.id
                
                # Fetch resources subcollection
                resources_ref = agents_ref.document(doc.id).collection("resources")
                resource_docs = resources_ref.stream()
                
                links = []
                async for r_doc in resource_docs:
                    try:
                        links.append(ResourceLink(**r_doc.to_dict()))
                    except Exception as e:
                        logger.warning(f"Skipping invalid resource link in session agent {doc.id}: {e}")
                
                agent_data["resource_links"] = links
                agents.append(AgentDefinition(**agent_data))

            logger.info(
                "Loaded session-local agents",
                extra={"session_id": session_id, "count": len(agents)},
            )
            return agents
        except Exception as e:
            logger.warning(
                "Failed to load session-local agents",
                extra={"session_id": session_id, "error": str(e)},
            )
            return []

    async def build_merged_agentset(
        self,
        user_ctx: UserContext,
        session_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """
        Build a merged agentset combining:
        1. System agents (from AgentRegistry)
        2. User-global agents
        3. Session-local agents (if session_id provided)

        Session-local agents override user-global, which override system.

        Args:
            user_ctx: User context with permissions and tier
            session_id: Optional session ID for session-local agents
            search: Optional search term (name/description/tags)

        Returns:
            Dictionary with merged agent metadata:
            {
                "agents": {
                    "agent_id": {
                        "agent_id": str,
                        "name": str,
                        "description": str,
                        "source": "system" | "user_global" | "session_local",
                        ...
                    }
                },
                "count": int
            }
        """
        from src.core.agent_registry import get_agent_registry

        agents: Dict[str, Dict[str, Any]] = {}

        # 1. Add system agents from registry
        agent_registry = get_agent_registry()
        is_admin = "admin" in user_ctx.permissions
        system_agents = agent_registry.list_available(
            user_tier=user_ctx.tier.value
            if isinstance(user_ctx.tier, Tier)
            else str(user_ctx.tier),
            user_id=user_ctx.user_id,
            is_admin=is_admin,
        )

        for metadata in system_agents:
            agents[metadata.agent_id] = {
                "agent_id": metadata.agent_id,
                "name": metadata.name,
                "description": metadata.description,
                "source": "system",
                "required_tier": metadata.required_tier,
                "enabled": metadata.enabled,
                "tags": list(metadata.tags),
                "default_model": metadata.default_model,
                "quota_cost_multiplier": metadata.quota_cost_multiplier,
            }

        # 2. Add user-global agents
        user_global_agents = await self.load_user_global_agents(user_ctx.user_id)
        for agent_def in user_global_agents:
            agents[agent_def.agent_id] = {
                "agent_id": agent_def.agent_id,
                "name": agent_def.name,
                "description": agent_def.description,
                "source": "user_global",
                "required_tier": "FREE",  # User agents accessible by owner
                "enabled": agent_def.enabled,
                "tags": list(agent_def.tags),
                "system_prompt": agent_def.system_prompt,
                "model": agent_def.model,
            }

        # 3. Add session-local agents (if session_id provided)
        if session_id:
            session_agents = await self.load_session_local_agents(user_ctx.user_id, session_id)
            for agent_def in session_agents:
                agents[agent_def.agent_id] = {
                    "agent_id": agent_def.agent_id,
                    "name": agent_def.name,
                    "description": agent_def.description,
                    "source": "session_local",
                    "required_tier": "FREE",  # Session agents accessible by owner
                    "enabled": agent_def.enabled,
                    "tags": list(agent_def.tags),
                    "system_prompt": agent_def.system_prompt,
                    "model": agent_def.model,
                }

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            filtered_agents = {}
            for k, v in agents.items():
                name = str(v.get("name", "")).lower()
                description = str(v.get("description", "")).lower()
                tags = v.get("tags", [])
                if isinstance(tags, list):
                    tag_matches = any(search_lower in str(tag).lower() for tag in tags)
                else:
                    tag_matches = search_lower in str(tags).lower()

                if search_lower in name or search_lower in description or tag_matches:
                    filtered_agents[k] = v
            agents = filtered_agents

        logger.info(
            "Built merged agentset", extra={"user_id": user_ctx.user_id, "count": len(agents)}
        )
        return {"agents": agents, "count": len(agents)}
