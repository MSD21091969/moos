"""
FastAPI Application - Agent Studio Backend

Features:
- Multi-user session support via SessionManager
- Approval workflow with DeferredToolRequests
- Tool event streaming (start/end)
- File upload and workspace management
- Todos sync to frontend
"""
import json
import logging
import uuid
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.tools import DeferredToolRequests

from app.deps import get_deps_for_session, release_session, DATA_DIR, SKILLS_DIR, USERS_ROOT
from app.agents.coordinator import get_coordinator_with_registered_subagents
from app.models import (
    UserMessage, AgentToken, StreamEnd, ErrorMessage,
    ToolStart, ToolEnd, ApprovalRequired, FileChanged, TodosUpdate, SkillsUpdate,
    UserContainer
)
import aiosqlite
from app.deps import DB_PATH
from app import db
from app import cache as cache_ops
from app.auth import Token, verify_password, create_access_token, verify_token, TokenData

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store pending approvals per session
_pending_approvals: dict[str, asyncio.Queue] = {}

# === WebSocket Manager & Concurrency ===

class ConnectionManager:
    def __init__(self):
        # active_connections: user_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # active_editors: canvas_id -> set(user_id)
        self.active_editors: dict[str, set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove user from all canvas locations
        empty_canvasses = []
        for canvas_id, editors in self.active_editors.items():
            if user_id in editors:
                editors.remove(user_id)
                if not editors:
                    empty_canvasses.append(canvas_id)
        
        for cid in empty_canvasses:
            del self.active_editors[cid]
            
    async def join_canvas(self, user_id: str, canvas_id: str):
        if canvas_id not in self.active_editors:
            self.active_editors[canvas_id] = set()
        self.active_editors[canvas_id].add(user_id)
        await self.broadcast_presence()

    async def leave_canvas(self, user_id: str, canvas_id: str):
        if canvas_id in self.active_editors:
            if user_id in self.active_editors[canvas_id]:
                self.active_editors[canvas_id].remove(user_id)
                if not self.active_editors[canvas_id]:
                    del self.active_editors[canvas_id]
        await self.broadcast_presence()

    async def broadcast_presence(self):
        """Broadcast the current list of active editors for all canvasses."""
        # Convert sets to lists for JSON serialization
        presence_data = {
            cid: list(editors) 
            for cid, editors in self.active_editors.items()
        }
        
        message = {
            "type": "presence_update",
            "editors": presence_data
        }
        
        # Broadcast to all connected clients
        to_remove = []
        for uid, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send presence to {uid}: {e}")
                to_remove.append(uid)
        
        # Cleanup broken connections
        for uid in to_remove:
            self.disconnect(uid)

manager = ConnectionManager()

# Auth Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await db.init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="Agent Studio",
    description="Integrated DeepAgent Application with multi-user support",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Auth Dependencies ===
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Validate token and return user data."""
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


# === Helper Functions ===
def get_session_dir(session_id: Optional[str], email: Optional[str] = None) -> str:
    """Get the persistent directory for a session. Prefers email for folder name if available."""
    if not session_id and not email:
        return DATA_DIR
    
    # Use email for folder name if provided, otherwise session_id
    dir_name = email if email else session_id
    path = os.path.join(USERS_ROOT, dir_name)
    os.makedirs(path, exist_ok=True)
    return path


def get_workspace_files(session_id: Optional[str] = None, email: Optional[str] = None) -> list[str]:
    """Get list of files in the workspace for a session."""
    files = []
    workspace_dir = get_session_dir(session_id, email)
    if os.path.exists(workspace_dir):
        for item in os.listdir(workspace_dir):
            if not item.startswith('.'):
                files.append(item)
    return files


def get_skills_list() -> list[str]:
    """Get list of loaded skills."""
    skills = []
    if os.path.exists(SKILLS_DIR):
        for item in os.listdir(SKILLS_DIR):
            skill_path = os.path.join(SKILLS_DIR, item)
            if os.path.isdir(skill_path) and os.path.exists(os.path.join(skill_path, "SKILL.md")):
                skills.append(item)
    return skills


# === Auth Endpoints ===
@app.post("/api/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and return JWT token."""
    user = await db.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["id"], "email": user["email"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


# === WebSocket Chat Endpoint ===
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    # Accept connection first to handle auth failure gracefully or via query param
    await websocket.accept()
    
    # Get token from query params
    token = websocket.query_params.get("token")
    user_data = None
    
    if token:
        user_data = verify_token(token)
    
    if not user_data:
        logger.warning("WebSocket connection attempt without valid token")
        await websocket.close(code=1008, reason="Authentication required")
        return

    # Use User ID as Session ID for persistence
    session_id = user_data.user_id
    logger.info(f"WebSocket connected: user={user_data.email} id={session_id}")
    
    # Register connection
    await manager.connect(websocket, session_id)
    
    # Get deps for this session (uses email for folder name if available)
    deps = await get_deps_for_session(session_id, user_data.email)
    coordinator = get_coordinator_with_registered_subagents(deps)
    conversation_id = None
    
    # Track session uploads separately from workspace
    session_uploads: list[str] = []
    
    # Create approval queue for this session
    approval_queue: asyncio.Queue = asyncio.Queue()
    _pending_approvals[session_id] = approval_queue
    
    # Send initial state
    await websocket.send_json(SkillsUpdate(skills=get_skills_list()).model_dump())
    
    # Broadcast initial presence (so new user gets current state)
    await manager.broadcast_presence()
    
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
            except Exception as e:
                logger.error(f"Invalid JSON: {e}")
                await websocket.send_json(ErrorMessage(detail=str(e)).model_dump())
                continue
            
            msg_type = data.get("type", "user")
            
            # Handle presence events
            if msg_type == "join_canvas":
                await manager.join_canvas(session_id, data.get("canvasId"))
                continue
                
            if msg_type == "leave_canvas":
                await manager.leave_canvas(session_id, data.get("canvasId"))
                continue
            
            # Handle reset
            if msg_type == "reset":
                conversation_id = None
                session_uploads = []
                await release_session(session_id)
                deps = await get_deps_for_session(session_id, user_data.email)
                coordinator = get_coordinator_with_registered_subagents(deps)
                logger.info(f"Session reset and sandbox refreshed: {session_id}")
                continue
            
            # Handle approval response
            if msg_type == "approval":
                approved = data.get("approved", False)
                await approval_queue.put(approved)
                logger.info(f"Approval received: {approved}")
                continue
            
            # Handle user message
            try:
                user_msg = UserMessage(**data)
            except Exception as e:
                logger.error(f"Invalid message: {e}")
                await websocket.send_json(ErrorMessage(detail=str(e)).model_dump())
                continue
            
            logger.info(f"Received: {user_msg.content[:50]}...")
            
            # Create conversation if needed
            if conversation_id is None:
                conversation_id = await db.create_conversation(user_msg.content[:50])
            
            # Save user message
            await db.add_message(conversation_id, "user", user_msg.content)
            
            # Stream agent response with tool events
            full_response = ""
            
            try:
                async with coordinator.run_stream(user_msg.content, deps=deps) as result:
                    async for chunk in result.stream():
                        full_response = str(chunk)
                        await websocket.send_json(AgentToken(content=full_response).model_dump())
                    
                    # Access output INSIDE the context manager
                    try:
                        final_output = result.output
                    except AttributeError:
                        # Fallback for older pydantic-ai versions
                        final_output = full_response
                    
                    # Check if agent needs approval (DeferredToolRequests)
                    if isinstance(final_output, DeferredToolRequests):
                        # Send approval requests to frontend
                        for req in final_output.tool_requests:
                            await websocket.send_json(ApprovalRequired(
                                id=req.tool_call_id,
                                action=req.tool_name,
                                details=json.dumps(req.args, default=str),
                            ).model_dump())
                        
                        # Wait for approval from frontend
                        try:
                            approved = await asyncio.wait_for(
                                approval_queue.get(),
                                timeout=300  # 5 minute timeout
                            )
                            
                            if approved:
                                # Resume with approval
                                # Note: This requires storing the run state - simplified for now
                                logger.info("Approval granted, continuing execution")
                            else:
                                full_response = "Operation cancelled by user."
                                await websocket.send_json(AgentToken(content=full_response).model_dump())
                        except asyncio.TimeoutError:
                            full_response = "Approval timeout - operation cancelled."
                            await websocket.send_json(AgentToken(content=full_response).model_dump())
                
                # Send current files list for this session
                current_files = get_workspace_files(session_id, user_data.email)
                await websocket.send_json(FileChanged(path="", action="list").model_dump())
                
                # Send todos if available
                if hasattr(deps, 'todos') and deps.todos:
                    todos_list = [{"text": str(t), "done": False} for t in deps.todos]
                    await websocket.send_json(TodosUpdate(todos=todos_list).model_dump())
                
                # Save agent response
                await db.add_message(conversation_id, "agent", full_response)
                await websocket.send_json(StreamEnd().model_dump())
                
            except UnexpectedModelBehavior as e:
                logger.error(f"Model error: {e}")
                await websocket.send_json(ErrorMessage(detail=str(e)).model_dump())
            except Exception as e:
                logger.error(f"Agent error: {e}")
                await websocket.send_json(ErrorMessage(detail=str(e)).model_dump())
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    finally:
        # Cleanup session
        _pending_approvals.pop(session_id, None)
        manager.disconnect(session_id)
        await manager.broadcast_presence()
        await release_session(session_id)


# === File Upload Endpoint ===
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), user: TokenData = Depends(get_current_user)):
    """Upload a file to staging (temp cache). Files stay in staging until explicit save."""
    try:
        session_id = user.email or user.user_id  # Use email as session ID
        
        # Store in temp cache (I:\system\.cache\{session}\)
        cache_dir = cache_ops.get_cache_dir(session_id)
        file_path = os.path.join(cache_dir, file.filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Uploaded file to cache: {file.filename} for session {session_id}")
        return {
            "status": "cached", 
            "filename": file.filename, 
            "path": file_path
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files")
async def list_files(user: TokenData = Depends(get_current_user)):
    """List files in the session's workspace."""
    return {"files": get_workspace_files(user.user_id, user.email)}


@app.get("/api/skills")
async def list_skills(user: TokenData = Depends(get_current_user)):
    """List available skills."""
    return {"skills": get_skills_list()}


@app.delete("/api/files/{filename}")
async def delete_file(filename: str, user: TokenData = Depends(get_current_user)):
    """Delete a file from the session's workspace."""
    session_id = user.user_id
    workspace_dir = get_session_dir(session_id, user.email)
    file_path = os.path.join(workspace_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Deleted file: {filename} from user session {session_id}")
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")


# === REST API Endpoints ===
@app.get("/api/conversations")
async def list_conversations(user: TokenData = Depends(get_current_user)):
    """List all conversations."""
    return await db.get_conversations()


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, user: TokenData = Depends(get_current_user)):
    """Get a conversation with its messages."""
    messages = await db.get_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"id": conversation_id, "messages": messages}


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, user: TokenData = Depends(get_current_user)):
    """Delete a conversation."""
    await db.delete_conversation(conversation_id)
    return {"status": "deleted"}


# === Canvasses API (DB-backed, multi-canvas) ===

def inject_canvas_metadata(canvas):
    """Helper to add AI-visible metadata to canvas data."""
    if not canvas:
        return canvas
    files = canvas.get("files", [])
    staging = [f for f in files if f.get("status") == "staging"]
    removed = [f for f in files if f.get("status") == "removed"]
    committed = [f for f in files if f.get("status") == "committed"]
    
    canvas["metadata"] = {
        "isDraft": len(staging) > 0 or len(removed) > 0,
        "stagingCount": len(staging),
        "removedCount": len(removed),
        "committedCount": len(committed)
    }
    return canvas


@app.get("/api/canvasses")
async def list_canvasses(user: TokenData = Depends(get_current_user)):
    """Get all canvasses for the current user. Creates default if none exist."""
    user_info = await db.get_user_by_id(user.user_id)
    display_name = user_info.get("display_name", "Lody") if user_info else "Lody"
    
    # Check if we should discover existing cache files (only if no canvasses in DB)
    canvasses_raw = await db.get_user_canvasses(user.user_id)
    discovered = None
    if not canvasses_raw:
        session_id = user.email or user.user_id
        filenames = cache_ops.list_cached_files(session_id)
        if filenames:
            discovered = []
            from datetime import datetime
            for f in filenames:
                discovered.append({
                    "id": str(uuid.uuid4()),
                    "name": f,
                    "sourcePath": f,
                    "sourceType": "local",
                    "fileType": "document" if "." in f and f.split(".")[-1].lower() in ["pdf", "doc", "docx", "txt"] else "other",
                    "addedAt": datetime.now().isoformat(),
                    "status": "staging"
                })
    
    # Ensure at least one canvas exists
    # DISABLED: User wants no canvases by default.
    # if not canvasses_raw:
    #     await db.ensure_default_canvas(user.user_id, display_name, discovered_files=discovered)
    #     canvasses_raw = await db.get_user_canvasses(user.user_id)
    
    return [inject_canvas_metadata(c) for c in canvasses_raw]


@app.post("/api/canvasses")
async def create_canvass(name: str = "New Canvas", container_id: str | None = None, user: TokenData = Depends(get_current_user)):
    """Create a new canvas for the user with unique name."""
    # Generate unique name if duplicate exists
    existing = await db.get_user_canvasses(user.user_id)
    existing_names = {c["name"] for c in existing}
    
    unique_name = name
    counter = 2
    while unique_name in existing_names:
        unique_name = f"{name} {counter}"
        counter += 1
    
    canvas = await db.create_canvas(user.user_id, unique_name, container_id=container_id)
    return canvas


@app.get("/api/canvasses/{canvas_id}")
async def get_canvass(canvas_id: str, user: TokenData = Depends(get_current_user)):
    """Get a specific canvas."""
    from app.acl_mock import check_container_access

    canvas = await db.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    # Check access: Owner OR Authorized via Container ACL
    if canvas["user_id"] != user.user_id:
        if not check_container_access(user.user_id, canvas.get("container_id")):
            raise HTTPException(status_code=403, detail="Access denied")
            
    return inject_canvas_metadata(canvas)


from pydantic import BaseModel

class CanvasUpdateRequest(BaseModel):
    name: str | None = None
    files: list | None = None
    container_id: str | None = None


@app.put("/api/canvasses/{canvas_id}")
async def update_canvass(canvas_id: str, req: CanvasUpdateRequest, user: TokenData = Depends(get_current_user)):
    """Update a canvas (name or files)."""
    from app.acl_mock import check_container_access

    canvas = await db.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    # Check access: Owner OR Authorized via Container ACL (Write access assumed for now)
    if canvas["user_id"] != user.user_id:
        if not check_container_access(user.user_id, canvas.get("container_id")):
            raise HTTPException(status_code=403, detail="Access denied")
    
    updated = await db.update_canvas(canvas_id, name=req.name, files=req.files, container_id=req.container_id)
    return updated


@app.delete("/api/canvasses/{canvas_id}")
async def delete_canvass(canvas_id: str, user: TokenData = Depends(get_current_user)):
    """Delete a canvas. Does NOT delete files from I: drive (mock registry: no refs)."""
    from app.acl_mock import check_container_access

    canvas = await db.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    # Check access: Owner OR Authorized via Container ACL
    if canvas["user_id"] != user.user_id:
        if not check_container_access(user.user_id, canvas.get("container_id")):
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Cleanup files before deleting canvas
    session_id = user.email or user.user_id
    cache_dir = cache_ops.get_cache_dir(session_id)
    user_dir = get_session_dir(user.user_id, user.email)
    
    for file in canvas.get("files", []):
        # Delete from cache if staging
        cache_path = os.path.join(cache_dir, file["name"])
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.info(f"Deleted cache file: {cache_path}")
        
        # Delete from user folder if committed (mock registry: always allowed)
        user_path = os.path.join(user_dir, file["name"])
        if os.path.exists(user_path):
            os.remove(user_path)
            logger.info(f"Deleted user file: {user_path}")
    
    await db.delete_canvas(canvas_id)
    return {"status": "deleted", "canvasId": canvas_id}


@app.post("/api/canvasses/{canvas_id}/commit")
async def commit_canvas(canvas_id: str, user: TokenData = Depends(get_current_user)):
    """Commit staged files: move from cache to permanent I:\\users\\{email} folder."""
    import shutil
    from app.acl_mock import check_container_access
    
    canvas = await db.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    # Check access: Owner OR Authorized via Container ACL
    if canvas["user_id"] != user.user_id:
        if not check_container_access(user.user_id, canvas.get("container_id")):
            raise HTTPException(status_code=403, detail="Access denied")
    
    session_id = user.email or user.user_id
    cache_dir = cache_ops.get_cache_dir(session_id)
    user_dir = get_session_dir(user.user_id, user.email)
    
    updated_files = []
    committed_count = 0
    purged_count = 0
    
    for file in canvas.get("files", []):
        status = file.get("status", "staging")
        
        if status == "removed":
            # Purge removed files from cache
            src = os.path.join(cache_dir, file["name"])
            if os.path.exists(src):
                os.remove(src)
                logger.info(f"Purged: {src}")
                purged_count += 1
            continue  # Don't add to updated_files
            
        if status == "staging":
            # Move file from cache to permanent storage
            src = os.path.join(cache_dir, file["name"])
            dst = os.path.join(user_dir, file["name"])
            
            if os.path.exists(src):
                # Ensure user_dir exists
                os.makedirs(user_dir, exist_ok=True)
                shutil.move(src, dst)
                file["uri"] = dst
                file["status"] = "committed"
                file.pop("cacheUri", None)
                committed_count += 1
                logger.info(f"Committed: {src} -> {dst}")
            else:
                logger.warning(f"Staged file missing from cache: {src}")
        
        updated_files.append(file)
    
    # Update canvas with cleaned-up file list and set draft to false
    await db.update_canvas(canvas_id, files=updated_files, is_draft=0)
    
    return {
        "status": "committed",
        "canvasId": canvas_id,
        "filesCommitted": committed_count,
        "totalFiles": len(updated_files)
    }

@app.post("/api/files/{filename}/open")
async def open_file_external(filename: str, user: TokenData = Depends(get_current_user)):
    """Open a file with the OS default application. Checks cache first, then stored."""
    import subprocess
    import platform
    
    session_id = user.email or user.user_id
    
    # Check cache first (staging files)
    cache_dir = cache_ops.get_cache_dir(session_id)
    cache_path = os.path.join(cache_dir, filename)
    
    # Then check permanent storage (committed files)
    user_dir = get_session_dir(user.user_id, user.email)
    stored_path = os.path.join(user_dir, filename)
    
    # Use whichever exists (prefer cache for active edits)
    if os.path.exists(cache_path):
        file_path = cache_path
    elif os.path.exists(stored_path):
        file_path = stored_path
    else:
        raise HTTPException(status_code=404, detail="File not found in cache or storage")
    
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", file_path])
        else:  # Linux
            subprocess.run(["xdg-open", file_path])
        
        logger.info(f"Opened file externally: {file_path}")
        return {"status": "opened", "filename": filename, "path": file_path}
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-studio", "version": "0.3.0"}



@app.get("/api/containers", response_model=list[UserContainer])
async def list_containers(user: TokenData = Depends(get_current_user)):
    """List containers owned by or shared with the current user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get owned + shared containers
        cursor = await db.execute("""
            SELECT c.* 
            FROM containers c
            LEFT JOIN container_acl acl ON c.id = acl.container_id
            WHERE c.owner_id = ? OR acl.grantee_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """, (user.user_id, user.user_id))
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# === Cache API Endpoints ===

@app.get("/api/cache/files/{filename}")
async def get_cached_file(filename: str, user: TokenData = Depends(get_current_user)):
    """Get content of a cached file."""
    session_id = user.user_id
    content = cache_ops.read_cached_file(session_id, filename)
    
    if content is None:
        raise HTTPException(status_code=404, detail="File not found in cache")
    
    return {"filename": filename, "content": content}


@app.delete("/api/cache/session")
async def clear_cache(user: TokenData = Depends(get_current_user)):
    """Clear all cached files for the session."""
    session_id = user.user_id
    cleared = cache_ops.clear_session_cache(session_id)
    
    return {"status": "cleared" if cleared else "nothing_to_clear"}


@app.get("/api/extract/{filename}")
async def extract_file_content(filename: str, user: TokenData = Depends(get_current_user)):
    """
    Extract text content from a file.
    First caches the file if not already cached, then extracts text.
    """
    session_id = user.user_id
    user_dir = get_session_dir(session_id, user.email)
    
    # Try cached file first
    cached_path = cache_ops.get_cached_file_path(session_id, filename)
    
    # If not cached, try to find in user workspace and cache it
    if not cached_path:
        source_path = os.path.join(user_dir, filename)
        if os.path.exists(source_path):
            cached_path = cache_ops.cache_file(session_id, source_path)
    
    if not cached_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    content = cache_ops.extract_text(cached_path)
    
    return {"filename": filename, "content": content}
