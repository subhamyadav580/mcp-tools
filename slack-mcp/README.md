# slack-mcp

A remote (streamable-http) MCP server wrapping the Slack Web API, so a TrueForge agent can
read and post to a Slack channel directly from a chat session.

## Tools

- `list_channels()` — channels (public + private) this bot is a member of.
- `list_channel_messages(channel?, limit=20)` — recent messages from a channel, newest first.
  Defaults to `SLACK_CHANNEL` if `channel` is omitted.
- `post_message(text, channel?)` — post a message. Defaults to `SLACK_CHANNEL` if omitted.

## Setup

Requires a Slack bot token (`xoxb-...`) with `channels:history`/`channels:read` (public) or
`groups:history`/`groups:read` (private) plus `chat:write`, invited into the target channel.

```bash
uv sync
cp .env.example .env   # fill in SLACK_BOT_TOKEN / SLACK_CHANNEL
uv run python main.py
```

Runs on `http://0.0.0.0:8002/mcp`. Register with TrueForge (running in Docker) at
`http://host.docker.internal:8002/mcp`.
