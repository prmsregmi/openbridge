import os
import httpx
from dataclasses import dataclass


HINTAS_BASE_URL = "https://app.hintas.com/api"


@dataclass
class DeployResult:
    mcp_url: str
    success: bool
    error: str | None = None


async def deploy_mcp(spec_url: str, api_base_url: str) -> DeployResult:
    """Deploy an OpenAPI spec as an MCP server via Hintas.

    In mock mode (MOCK_HINTAS=true), returns a configurable MCP URL
    without hitting the real API.
    """
    if os.getenv("MOCK_HINTAS", "").lower() == "true":
        mock_url = os.getenv("MOCK_MCP_URL", "http://localhost:3000/mcp")
        return DeployResult(mcp_url=mock_url, success=True)

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{HINTAS_BASE_URL}/deploy",
            json={"spec_url": spec_url, "api_base_url": api_base_url},
        )

        if resp.status_code != 200:
            return DeployResult(
                mcp_url="",
                success=False,
                error=f"Hintas API returned {resp.status_code}: {resp.text}",
            )

        data = resp.json()
        return DeployResult(mcp_url=data["mcp_url"], success=True)
