"""Built-in tool definitions for the OpenBridge agent.

These are the tools available BEFORE any MCP is deployed.
They let Claude search for specs and trigger deployment.
"""

BUILTIN_TOOLS = [
    {
        "name": "search_apis",
        "description": (
            "Search for OpenAPI specifications by software/service name. "
            "Returns a list of matching APIs with their spec URLs and base URLs. "
            "Try this first before other search methods."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Name of the software or API to search for (e.g., 'Notion', 'Stripe', 'Slack')",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_github_specs",
        "description": (
            "Search GitHub repositories for OpenAPI spec files. "
            "Use this if search_apis doesn't find what you need. "
            "Searches for openapi.yaml and swagger.json files."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Name of the software or API to search for",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "deploy_mcp",
        "description": (
            "Deploy a Hintas project as an MCP server. "
            "Requires the project_id (UUID) of an existing Hintas project. "
            "Returns the MCP endpoint URL on success."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The Hintas project UUID to deploy",
                },
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "connect_mcp",
        "description": (
            "Connect to a deployed MCP server and discover its available tools. "
            "After this succeeds, new tools from the MCP will be available. "
            "Call this after deploy_mcp returns an MCP URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mcp_url": {
                    "type": "string",
                    "description": "The MCP endpoint URL returned by deploy_mcp",
                }
            },
            "required": ["mcp_url"],
        },
    },
]
