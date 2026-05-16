---
name: openbridge
version: 0.1.0
description: |
  Find any API's OpenAPI spec and deploy it as an MCP server via Hintas.
  Use when asked to "integrate with", "connect to", "add API for".
  (gstack)
triggers:
  - integrate with a service
  - connect to an API
  - deploy MCP for
  - openbridge
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# /openbridge — Self-Extending API Integration

Finds OpenAPI specs for any software and deploys them as MCP servers, giving you new capabilities on-the-fly.

## Workflow

1. Ask the user what service they want to integrate with:

```
AskUserQuestion: "What software or API would you like to integrate with?"
```

2. Run the OpenBridge agent:

```bash
cd /Users/prms/Projects/openbridge && uv run python main.py "$USER_INPUT"
```

3. Report the results. If an MCP was deployed successfully, inform the user of the new MCP URL and available tools.
