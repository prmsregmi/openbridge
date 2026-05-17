from dataclasses import dataclass, field
from typing import Any

import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession


@dataclass
class McpTool:
    name: str
    description: str
    input_schema: dict


@dataclass
class McpBridge:
    """Manages a live connection to a deployed MCP server."""

    url: str
    tools: list[McpTool] = field(default_factory=list)
    _session: ClientSession | None = field(default=None, repr=False)
    _session_context: Any = field(default=None, repr=False)
    _transport_context: Any = field(default=None, repr=False)

    async def connect(self) -> list[McpTool]:
        """Connect to MCP server and discover available tools."""
        self._http_client = httpx.AsyncClient(verify=False, follow_redirects=True)
        await self._http_client.__aenter__()

        self._transport_context = streamable_http_client(
            self.url, http_client=self._http_client
        )
        try:
            streams = await self._transport_context.__aenter__()
            read_stream, write_stream = streams[0], streams[1]
        except Exception:
            self._transport_context = None
            await self._http_client.__aexit__(None, None, None)
            raise

        try:
            self._session_context = ClientSession(read_stream, write_stream)
            self._session = await self._session_context.__aenter__()
            await self._session.initialize()
        except Exception:
            await self._transport_context.__aexit__(None, None, None)
            self._transport_context = None
            self._session_context = None
            raise

        tools_response = await self._session.list_tools()
        self.tools = [
            McpTool(
                name=t.name,
                description=t.description or "",
                input_schema=t.inputSchema or {"type": "object", "properties": {}},
            )
            for t in tools_response.tools
        ]
        return self.tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Execute a tool on the MCP server."""
        if not self._session:
            raise RuntimeError("Not connected. Call connect() first.")

        result = await self._session.call_tool(name, arguments=arguments)
        # MCP returns content as a list of content blocks
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts)

    async def disconnect(self):
        """Clean up the MCP connection."""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._transport_context:
            await self._transport_context.__aexit__(None, None, None)
        if hasattr(self, "_http_client") and self._http_client:
            await self._http_client.__aexit__(None, None, None)

    def to_anthropic_tools(self) -> list[dict]:
        """Convert MCP tools to Anthropic API tool format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools
        ]
