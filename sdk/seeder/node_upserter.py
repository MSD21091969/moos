"""node_upserter — upsert AgentWorkspace context into ColliderDataServer nodes.

Calls the DataServer REST API to:
  1. Authenticate (POST /auth/login) and obtain a JWT.
  2. Ensure the target Application exists (GET /api/v1/apps/).
  3. For each AgentWorkspace (parent-first BFS order):
     - Resolve parent Node ID from the path map.
     - GET /api/v1/apps/{app_id}/nodes/ to find an existing node by path.
     - If found: PATCH /api/v1/apps/{app_id}/nodes/{node_id}
     - If not:   POST /api/v1/apps/{app_id}/nodes/
  4. Register each tool in the workspace with GraphToolServer
     (POST /api/v1/registry/tools) so ToolRunner can execute them.
  5. Return a mapping of node_path → node_id for downstream use.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .agent_walker import AgentWorkspace

logger = logging.getLogger(__name__)


class NodeUpserter:
    """HTTP client wrapper around ColliderDataServer node CRUD endpoints."""

    def __init__(
        self,
        data_server_url: str,
        username: str,
        password: str,
        app_id: str,
        dry_run: bool = False,
        graph_server_url: str = "http://localhost:8001",
    ) -> None:
        self.base = data_server_url.rstrip("/")
        self.graph_base = graph_server_url.rstrip("/")
        self.username = username
        self.password = password
        self.app_id = app_id
        self.dry_run = dry_run
        self._token: str | None = None
        self._user_id: str | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._token:
            return self._token
        resp = await client.post(
            f"{self.base}/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._user_id = data.get("user", {}).get("id", "seeder")
        return self._token  # type: ignore[return-value]

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    # ------------------------------------------------------------------
    # Node CRUD
    # ------------------------------------------------------------------

    async def _list_nodes(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        resp = await client.get(
            f"{self.base}/api/v1/apps/{self.app_id}/nodes/",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]

    async def _create_node(
        self,
        client: httpx.AsyncClient,
        path: str,
        parent_id: str | None,
        container: dict[str, Any],
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"path": path, "container": container}
        if parent_id:
            body["parent_id"] = parent_id
        resp = await client.post(
            f"{self.base}/api/v1/apps/{self.app_id}/nodes/",
            json=body,
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]

    async def _update_node(
        self,
        client: httpx.AsyncClient,
        node_id: str,
        container: dict[str, Any],
    ) -> dict[str, Any]:
        resp = await client.patch(
            f"{self.base}/api/v1/apps/{self.app_id}/nodes/{node_id}",
            json={"container": container},
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Tool registration in GraphToolServer
    # ------------------------------------------------------------------

    async def _register_tool(
        self,
        client: httpx.AsyncClient,
        tool: dict[str, Any],
        node_id: str,
    ) -> None:
        """POST a ToolDefinition to the GraphToolServer tool registry.

        GraphStepEntry fields mapped from ToolDefinition:
          tool_name      ← tool["name"]
          code_ref       ← tool["code_ref"]
          params_schema  ← tool["params_schema"]
          visibility     ← tool.get("visibility", "global")
          origin_node_id ← node_id (the DataServer node that owns this tool)
          owner_user_id  ← self._user_id (the seeder's authenticated user)
        """
        payload: dict[str, Any] = {
            "tool_name": str(tool.get("name", "")),
            "origin_node_id": node_id,
            "owner_user_id": self._user_id or "seeder",
            "params_schema": dict(tool.get("params_schema") or {}),
            "code_ref": str(tool.get("code_ref", "")),
            "visibility": str(tool.get("visibility", "global")),
        }
        try:
            resp = await client.post(
                f"{self.graph_base}/api/v1/registry/tools",
                json=payload,
                timeout=10.0,
            )
            if resp.status_code in (200, 201):
                logger.debug("Registered tool: %s (node=%s)", tool["name"], node_id)
            elif resp.status_code == 409:
                logger.debug("Tool already registered: %s", tool["name"])
            else:
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Failed to register tool %s: %s — %s",
                tool.get("name"),
                exc.response.status_code,
                exc.response.text[:200],
            )
        except httpx.RequestError as exc:
            logger.warning(
                "GraphToolServer unreachable, skipping tool registration for %s: %s",
                tool.get("name"),
                exc,
            )

    # ------------------------------------------------------------------
    # Container builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_container(ws: AgentWorkspace) -> dict[str, Any]:
        return {
            "version": "1.0.0",
            "kind": "workspace",
            "species": "ide",
            "instructions": ws.instructions,
            "rules": ws.rules,
            "knowledge": ws.knowledge,
            "skills": ws.skills,
            "tools": ws.tools,
            "workflows": [],
            "configs": {},
            "manifest": {"name": ws.manifest_name, "node_path": ws.node_path},
        }

    # ------------------------------------------------------------------
    # Main upsert loop
    # ------------------------------------------------------------------

    async def upsert_all(
        self, workspaces: list[AgentWorkspace]
    ) -> dict[str, str]:
        """Upsert all workspaces into the DataServer in parent-first order.

        After each node upsert, registers any tools in the workspace with the
        GraphToolServer so ToolRunner can execute them via importlib.

        Args:
            workspaces: BFS-ordered list of AgentWorkspace objects.

        Returns:
            Mapping of ``node_path → node_id`` for all upserted nodes.
        """
        node_path_to_id: dict[str, str] = {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self._get_token(client)

            # Build lookup of existing nodes by path
            existing: dict[str, str] = {}
            try:
                for n in await self._list_nodes(client):
                    existing[n["path"]] = n["id"]
            except httpx.HTTPStatusError as exc:
                logger.warning("Could not list nodes: %s", exc)

            for ws in workspaces:
                container = self._build_container(ws)
                parent_id = (
                    node_path_to_id.get(ws.parent_node_path)
                    if ws.parent_node_path
                    else None
                )

                if self.dry_run:
                    action = "UPDATE" if ws.node_path in existing else "CREATE"
                    logger.info(
                        "[dry-run] %s node: path=%s  parent_id=%s  "
                        "instructions=%d  rules=%d  knowledge=%d  skills=%d  tools=%d",
                        action,
                        ws.node_path,
                        parent_id,
                        len(ws.instructions),
                        len(ws.rules),
                        len(ws.knowledge),
                        len(ws.skills),
                        len(ws.tools),
                    )
                    # Use a placeholder id so children can still resolve parent
                    node_path_to_id[ws.node_path] = existing.get(ws.node_path, f"dry-{ws.node_path}")
                    continue

                try:
                    if ws.node_path in existing:
                        node_id = existing[ws.node_path]
                        await self._update_node(client, node_id, container)
                        logger.info(
                            "Updated node: path=%s  id=%s  tools=%d",
                            ws.node_path, node_id, len(ws.tools),
                        )
                    else:
                        result = await self._create_node(
                            client, ws.node_path, parent_id, container
                        )
                        node_id = result["id"]
                        logger.info(
                            "Created node: path=%s  id=%s  tools=%d",
                            ws.node_path, node_id, len(ws.tools),
                        )

                    node_path_to_id[ws.node_path] = node_id

                    # Register tools with GraphToolServer
                    for tool in ws.tools:
                        await self._register_tool(client, tool, node_id)

                except httpx.HTTPStatusError as exc:
                    logger.error(
                        "Failed to upsert node %s: %s — %s",
                        ws.node_path,
                        exc.response.status_code,
                        exc.response.text[:200],
                    )

        return node_path_to_id
