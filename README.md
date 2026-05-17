# OpenBridge

**An agent that connects to any API by deploying MCP interfaces directly from the provider's own OpenAPI specification.**

Describe what you want to integrate. The agent finds the official spec, deploys a verified MCP server from it via [Hintas](https://hintas.com), and immediately gains new capabilities — all within a single conversation.

## How It Works

```
User: "I need to search breweries"
  │
  ├─ 1. DISCOVER    → Find the official OpenAPI spec (APIs.guru, GitHub)
  ├─ 2. DEPLOY      → Hintas generates an MCP server from the spec
  ├─ 3. EXTEND      → Agent connects, discovers available endpoints
  └─ 4. EXECUTE     → Agent calls real API endpoints through verified MCP
```

The agent doesn't load entire API specs into context. It deploys a targeted MCP interface and calls only what it needs, when it needs it. This is a search-and-execute approach — API specs can be tens of thousands of lines, but the agent only interacts with the endpoints relevant to the task.

Every tool the agent gains maps 1:1 to a real, documented endpoint from the provider's own specification. Not a third-party reimplementation, not a community-maintained wrapper — the actual API surface, generated directly from the source of truth. When the provider updates their spec, regenerating picks up changes immediately.

## Architecture

| Component | Role |
|-----------|------|
| `src/agent.py` | Claude-powered agent loop with dynamic tool extension |
| `src/spec_finder.py` | Multi-strategy spec discovery (APIs.guru → GitHub) |
| `src/hintas.py` | Deploys specs as verified MCP servers |
| `src/mcp_bridge.py` | Connects to deployed MCPs via streamable HTTP |
| `skill/SKILL.md` | GStack skill wrapper — invoke as `/openbridge` |

## GStack & GBrain

- **GStack**: OpenBridge is a GStack skill. Run `/openbridge` in any GStack-enabled agent (Claude Code, Hermes, OpenClaw) for the full flow within your session.
- **GBrain**: Persists discovered specs and successful deployments as knowledge, accelerating future integrations through brain-first lookup.

## Setup

```bash
git clone https://github.com/prmsregmi/openbridge.git && cd openbridge
cp .env.example .env
uv sync
```

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Powers the agent (required) |
| `HINTAS_API_KEY` | Deploys MCP servers (required for deployment) |
| `GITHUB_TOKEN` | Better rate limits on spec search (optional) |

## Usage

```bash
uv run python main.py "I want to connect to the Notion API"
```

## License

MIT
