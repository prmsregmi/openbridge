import os
import httpx
from dataclasses import dataclass


HINTAS_BASE_URL = "https://app.hintas.com"


def _get_headers() -> dict:
    api_key = os.getenv("HINTAS_API_KEY", "")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


@dataclass
class ProjectResult:
    project_id: str
    name: str
    has_spec: bool
    success: bool
    error: str | None = None


@dataclass
class DeployResult:
    mcp_url: str
    project_url: str
    project_id: str
    status: str
    success: bool
    error: str | None = None


async def create_project(name: str, spec_url: str, upstream_url: str = "") -> ProjectResult:
    """Create a Hintas project with an OpenAPI spec attached.

    Passing spec_url during creation validates and attaches the spec in one call.
    """
    if os.getenv("MOCK_HINTAS", "").lower() == "true":
        return ProjectResult(
            project_id="mock-project-id",
            name=name,
            has_spec=True,
            success=True,
        )

    body: dict = {"name": name}
    if spec_url:
        body["spec_url"] = spec_url
    if upstream_url:
        body["upstream_url"] = upstream_url

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{HINTAS_BASE_URL}/api/projects",
            json=body,
            headers=_get_headers(),
        )

        if resp.status_code not in (200, 201):
            return ProjectResult(
                project_id="",
                name=name,
                has_spec=False,
                success=False,
                error=f"HTTP {resp.status_code}: {resp.text}",
            )

        data = resp.json()
        return ProjectResult(
            project_id=data["id"],
            name=data.get("name", name),
            has_spec=data.get("has_spec", bool(spec_url)),
            success=True,
        )


async def deploy_project(project_id: str) -> DeployResult:
    """Deploy a Hintas project. Project must have a valid spec attached."""
    if os.getenv("MOCK_HINTAS", "").lower() == "true":
        mock_url = os.getenv("MOCK_MCP_URL", "http://localhost:3000/mcp")
        return DeployResult(
            mcp_url=mock_url,
            project_url=mock_url.replace("/mcp", ""),
            project_id=project_id,
            status="queued",
            success=True,
        )

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{HINTAS_BASE_URL}/api/deploy",
            json={"project_id": project_id},
            headers=_get_headers(),
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
