# postgres-mcp

A remote (streamable-http) MCP server wrapping read-only Postgres access, so a TrueForge
agent can query a database directly from a chat session.

## Tools

- `list_tables()` — tables in the `public` schema.
- `fetch_one(query, params?)` — run a `SELECT`/`WITH` query, return the first row.
- `fetch_all(query, params?)` — run a `SELECT`/`WITH` query, return all rows.

Only `SELECT`/`WITH` queries are allowed — `validate_query()` in `main.py` rejects any
DML/DDL keyword (`insert`, `update`, `delete`, `drop`, `alter`, ...) and multi-statement
queries before they ever reach the database.

## Setup

```bash
uv sync
cp .env.example .env   # fill in DATABASE_URL
uv run python main.py
```

Runs on `http://0.0.0.0:8000/mcp`. Register with TrueForge (running in Docker) at
`http://host.docker.internal:8000/mcp`.
