---
name: hintas
version: 0.1.0
description: |
  Deploy any OpenAPI spec as a live MCP server via Hintas.
  Use when asked to "deploy an API", "create MCP server", "connect to hintas".
  (openbridge)
triggers:
  - deploy API as MCP
  - create MCP server from spec
  - hintas deploy
  - connect api to hintas
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# /hintas — Deploy OpenAPI Specs as MCP Servers

Deploys any OpenAPI specification as a live, verified MCP server through Hintas. The MCP interface is generated directly from the provider's own spec — not a third-party wrapper.

## Prerequisites

The agent needs a Hintas API key with `projects:write`, `specs:write`, and `deploy:write` scopes.

## Setup

Check if the key is already configured:

```bash
grep -q HINTAS_API_KEY .env 2>/dev/null && echo "Key found" || echo "No key"
```

If no key is found, ask the user:

```
AskUserQuestion: "I need your Hintas API key to deploy MCP servers. You can create one at app.hintas.com → Team Settings → API Keys (needs Deploy or Full access scope). Paste it here:"
```

Once the user provides the key, store it in the project `.env`:

```bash
echo "HINTAS_API_KEY=$USER_PROVIDED_KEY" >> .env
```

Never print, log, or pass the API key to an LLM. It is only used in HTTP request headers.

## Workflow

### Step 1: Identify the spec

The user should provide either:
- A spec URL (e.g., `https://api.example.com/openapi.json`)
- A software name to search for

If they provide a name, search for the spec:

```bash
uv run python -c "
import asyncio
from dotenv import load_dotenv
load_dotenv()
from src.spec_finder import find_spec

async def search():
    results = await find_spec('$QUERY')
    for r in results[:5]:
        print(f'{r.name} | {r.spec_url} | {r.api_base_url}')

asyncio.run(search())
"
```

### Step 2: Create project and deploy

```bash
uv run python -c "
import asyncio
from dotenv import load_dotenv
load_dotenv()
from src.hintas import create_project, deploy_project

async def deploy():
    project = await create_project(
        name='$PROJECT_NAME',
        spec_url='$SPEC_URL',
        upstream_url='$UPSTREAM_URL'
    )
    if not project.success:
        print(f'ERROR: {project.error}')
        return

    result = await deploy_project(project.project_id)
    if not result.success:
        print(f'ERROR: {result.error}')
        return

    print(f'MCP_URL={result.mcp_url}')
    print(f'PROJECT_URL={result.project_url}')
    print(f'STATUS={result.status}')

asyncio.run(deploy())
"
```

### Step 3: Connect to the MCP

Once deployed, the MCP is available at the returned URL. Add it to the agent's MCP configuration or connect directly:

```bash
uv run python -c "
import asyncio
from src.mcp_bridge import McpBridge

async def connect():
    bridge = McpBridge(url='$MCP_URL')
    tools = await bridge.connect()
    print(f'Connected. {len(tools)} tools available:')
    for t in tools:
        print(f'  {t.name}: {t.description[:80]}')

asyncio.run(connect())
"
```

## API Reference

| Endpoint | Method | Body | Response |
|----------|--------|------|----------|
| `/api/projects` | POST | `{name, spec_url?, upstream_url?}` | `{id, name, has_spec}` |
| `/api/specs` | POST | `{project_id, spec_url}` | `{openapi_path, displayName}` |
| `/api/deploy` | POST | `{project_id}` | `{mcp_url, url, status}` |

All endpoints require `Authorization: Bearer sk_live_...` header.

## Constraints

- Project names must be lowercase slugs (3-63 chars, alphanumeric + hyphens)
- Specs must be valid OpenAPI 2.0/3.x (JSON or YAML), max 10 MB
- Deployment status starts as "queued" — the MCP endpoint may take 10-30 seconds to become available
- Rate limit: 100 requests/minute per key
