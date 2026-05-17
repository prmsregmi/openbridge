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
        "name": "create_and_deploy",
        "description": (
            "Create a Hintas project from an OpenAPI spec URL and deploy it as an MCP server. "
            "This is a two-step process: creates the project with the spec, then deploys it. "
            "Returns the MCP endpoint URL on success. Use after finding a spec URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Short lowercase slug for the project (e.g., 'notion-api', 'open-brewery-db')",
                },
                "spec_url": {
                    "type": "string",
                    "description": "URL of the OpenAPI spec to deploy",
                },
                "upstream_url": {
                    "type": "string",
                    "description": "Base URL of the actual API (e.g., 'https://api.notion.com')",
                },
            },
            "required": ["name", "spec_url"],
        },
    },
    {
        "name": "connect_mcp",
        "description": (
            "Connect to a deployed MCP server and discover its available tools. "
            "After this succeeds, new tools from the MCP will be available. "
            "Call this after create_and_deploy returns an MCP URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mcp_url": {
                    "type": "string",
                    "description": "The MCP endpoint URL returned by create_and_deploy",
                }
            },
            "required": ["mcp_url"],
        },
    },
]
