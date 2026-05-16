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
            "Deploy an OpenAPI spec as an MCP server via Hintas. "
            "Requires the spec URL and the API's base URL. "
            "Returns the MCP endpoint URL on success."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spec_url": {
                    "type": "string",
                    "description": "URL where the OpenAPI spec is hosted",
                },
                "api_base_url": {
                    "type": "string",
                    "description": "Base URL of the actual API (e.g., https://api.notion.com)",
                },
            },
            "required": ["spec_url", "api_base_url"],
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
