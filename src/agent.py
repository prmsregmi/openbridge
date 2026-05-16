import os
import asyncio
from typing import Any

from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.spec_finder import find_spec, search_github_specs as github_search
from src.hintas import deploy_mcp as hintas_deploy
from src.mcp_bridge import McpBridge
from src.tools import BUILTIN_TOOLS

console = Console()

SYSTEM_PROMPT = """You are OpenBridge, an agent that helps users connect to any software by finding its API specification and deploying it as an MCP server.

Your workflow:
1. When the user describes software they want to integrate, search for its OpenAPI spec using search_apis first.
2. If search_apis doesn't find it, try search_github_specs.
3. Once you find a spec, use deploy_mcp with the spec_url and api_base_url.
4. After deployment, use connect_mcp with the returned MCP URL.
5. Once connected, you'll gain new tools from the MCP. Demonstrate one of them to show the integration works.

Be concise. Show progress. When you discover new tools after connecting, list them briefly and then use one to demonstrate the new capability."""


class Agent:
    def __init__(self):
        self.client = Anthropic()
        self.messages: list[dict[str, Any]] = []
        self.mcp_bridge: McpBridge | None = None
        self.dynamic_tools: list[dict] = []

    def _get_tools(self) -> list[dict]:
        return BUILTIN_TOOLS + self.dynamic_tools

    async def _handle_tool_call(self, name: str, args: dict) -> str:
        """Route tool calls to the appropriate handler."""
        if name == "search_apis":
            results = await find_spec(args["query"], os.getenv("GITHUB_TOKEN"))
            if not results:
                return "No specs found for that query."
            lines = []
            for r in results:
                lines.append(
                    f"- **{r.name}** ({r.source})\n"
                    f"  Spec: {r.spec_url}\n"
                    f"  API Base: {r.api_base_url}\n"
                    f"  {r.description[:100]}"
                )
            return "\n".join(lines)

        elif name == "search_github_specs":
            results = await github_search(args["query"], os.getenv("GITHUB_TOKEN"))
            if not results:
                return "No specs found on GitHub for that query."
            lines = []
            for r in results:
                lines.append(f"- **{r.name}**\n  Spec: {r.spec_url}")
            return "\n".join(lines)

        elif name == "deploy_mcp":
            result = await hintas_deploy(args["spec_url"], args["api_base_url"])
            if not result.success:
                return f"Deployment failed: {result.error}"
            return f"MCP deployed successfully.\nMCP URL: {result.mcp_url}"

        elif name == "connect_mcp":
            self.mcp_bridge = McpBridge(url=args["mcp_url"])
            try:
                tools = await self.mcp_bridge.connect()
                self.dynamic_tools = self.mcp_bridge.to_anthropic_tools()
                tool_names = [t.name for t in tools]
                return (
                    f"Connected to MCP. Discovered {len(tools)} new tools:\n"
                    + ", ".join(tool_names)
                    + "\n\nThese tools are now available for use."
                )
            except Exception as e:
                return f"Failed to connect to MCP: {e}"

        else:
            # Must be a dynamic MCP tool
            if self.mcp_bridge:
                try:
                    result = await self.mcp_bridge.call_tool(name, args)
                    return result
                except Exception as e:
                    return f"MCP tool call failed: {e}"
            return f"Unknown tool: {name}"

    async def run(self, user_input: str) -> None:
        """Run the agent loop with the given user input."""
        self.messages.append({"role": "user", "content": user_input})

        console.print(
            Panel(user_input, title="[bold blue]User Input", border_style="blue")
        )

        while True:
            console.print("\n[dim]Thinking...[/dim]")

            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=self._get_tools(),
                messages=self.messages,
            )

            # Display and collect tool uses from response
            tool_uses = []
            for block in response.content:
                if block.type == "text" and block.text:
                    console.print(Markdown(block.text))
                elif block.type == "tool_use":
                    tool_uses.append(block)
                    console.print(
                        f"\n[bold yellow]⚡ Calling tool:[/bold yellow] {block.name}"
                    )
                    if block.input:
                        for k, v in block.input.items():
                            val = str(v)[:80]
                            console.print(f"   [dim]{k}:[/dim] {val}")

            # Add full response content to history (SDK handles serialization)
            self.messages.append({"role": "assistant", "content": response.content})

            # If no tool calls, we're done
            if response.stop_reason != "tool_use":
                break

            # Execute tool calls and add results
            tool_results = []
            for tool_use in tool_uses:
                result_text = await self._handle_tool_call(
                    tool_use.name, tool_use.input
                )
                console.print(f"\n[green]✓ {tool_use.name} result:[/green]")
                # Truncate display for readability
                display = result_text[:500] + ("..." if len(result_text) > 500 else "")
                console.print(f"  [dim]{display}[/dim]")

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": [{"type": "text", "text": result_text}],
                    }
                )

            self.messages.append({"role": "user", "content": tool_results})

        # Cleanup
        if self.mcp_bridge:
            try:
                await self.mcp_bridge.disconnect()
            except Exception:
                pass
