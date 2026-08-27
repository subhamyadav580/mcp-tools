# mcp-tools

Remote MCP servers for the TrueForge incident-responder agent (see the [Agent Harness
Hackathon](https://www.wemakedevs.org/hackathons/trueforge)). TrueForge only connects to
**remote** (HTTP) MCP servers — it cannot spawn a local stdio process — so each of these
runs as its own small HTTP service and gets registered with TrueForge by URL.

## Servers

| Server | Port | Tools | Purpose |
|---|---|---|---|
| [`postgres-mcp`](postgres-mcp/) | 8000 | `list_tables`, `fetch_one`, `fetch_all` | Read-only Postgres queries (`SELECT`/`WITH` only, enforced) |
| [`elastic-mcp`](elastic-mcp/) | 8001 | `list_es_indices`, `get_index_mapping`, `search_on_index` | Read-only Elasticsearch log search |
| [`slack-mcp`](slack-mcp/) | 8002 | `list_channels`, `list_channel_messages`, `post_message`, `get_thread_replies` | Read Slack alerts, post/thread updates back |

All three follow the same pattern: [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
(`mcp<2` — the 2.x release renamed `FastMCP`, pin below that), `streamable-http` transport,
bound to `0.0.0.0` so a Dockerized TrueForge can reach them via `host.docker.internal`,
managed with `uv`.

## Setup (per server)

Each server directory has its own `README.md` with exact tool/setup details. The short version:

```bash
cd <server>
uv sync
cp .env.example .env   # fill in real credentials — never commit this file
uv run python main.py
```

## Registering with TrueForge

Once a server is running, register it as a `remote` MCP connector:

```bash
curl -s -X POST http://localhost:8791/api/v1/settings/mcp-servers \
  -H "Content-Type: application/json" \
  -d '{
    "manifest": {
      "type": "remote",
      "name": "<server-name>",
      "url": "http://host.docker.internal:<port>/mcp",
      "description": "<what it does>"
    }
  }'
```

Then attach it to an agent by name in `mcp_servers: [{ "name": "<server-name>" }]`. See
[docs/create-agent/overview.mdx](../trueforge/docs/create-agent/overview.mdx) in the
TrueForge repo for the full agent spec.

## Adding a new server

Copy the shape of an existing one (`slack-mcp` is the simplest reference), pick the next
free port (currently 8003+), and add a row to the table above.
