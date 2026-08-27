# elastic-mcp

A remote (streamable-http) MCP server wrapping read-only Elasticsearch access, so a
TrueForge agent can search application logs directly from a chat session.

## Tools

- `list_es_indices()` — all available indices.
- `get_index_mapping(index_name)` — field names and types for an index. Call this before
  `search_on_index` so queries use real field names/types.
- `search_on_index(index_name, query)` — run an Elasticsearch query DSL search, return the
  raw response (hits, scores, `_source` documents).

## Setup

```bash
uv sync
cp .env.example .env   # fill in ELASTIC_URL
uv run python main.py
```

Runs on `http://0.0.0.0:8001/mcp`. Register with TrueForge (running in Docker) at
`http://host.docker.internal:8001/mcp`.
