import os
import httpx
from dataclasses import dataclass


HINTAS_BASE_URL = "https://app.hintas.com"


@dataclass
class DeployResult:
    mcp_url: str
    project_url: str
    project_id: str
    status: str
    success: bool
    error: str | None = None


async def deploy_project(project_id: str) -> DeployResult:
    """Deploy a Hintas project and get its MCP endpoint.

    Requires HINTAS_API_KEY env var (sk_live_... with deploy:write scope).
    In mock mode (MOCK_HINTAS=true), returns a configurable MCP URL.
    """
    if os.getenv("MOCK_HINTAS", "").lower() == "true":
        mock_url = os.getenv("MOCK_MCP_URL", "http://localhost:3000/mcp")
        return DeployResult(
            mcp_url=mock_url,
            project_url=mock_url.replace("/mcp", ""),
            project_id=project_id,
            status="queued",
            success=True,
        )

    api_key = os.getenv("HINTAS_API_KEY")
    if not api_key:
        return DeployResult(
            mcp_url="",
            project_url="",
            project_id=project_id,
            status="error",
            success=False,
            error="HINTAS_API_KEY not set",
        )

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{HINTAS_BASE_URL}/api/deploy",
            json={"project_id": project_id},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        if resp.status_code != 200:
            return DeployResult(
                mcp_url="",
                project_url="",
                project_id=project_id,
                status="error",
                success=False,
                error=f"HTTP {resp.status_code}: {resp.text}",
            )

        data = resp.json()
        return DeployResult(
            mcp_url=data["mcp_url"],
            project_url=data.get("url", ""),
            project_id=data["project_id"],
            status=data.get("status", "queued"),
            success=True,
        )
