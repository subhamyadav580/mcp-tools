from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from slack_sdk.errors import SlackApiError

from slack_client import DEFAULT_CHANNEL, slack_instance

mcp = FastMCP("Slack MCP Server", host="0.0.0.0", port=8002)

client = slack_instance.get_client()


@mcp.tool()
async def list_channels() -> list[dict[str, Any]]:
    """
    List channels (public and private) that this bot is a member of.
    Call this first if you don't already know the channel id to use.
    """
    channels: list[dict[str, Any]] = []
    for types in ("public_channel", "private_channel"):
        cursor = None
        while True:
            try:
                response = client.conversations_list(types=types, limit=200, cursor=cursor)
            except SlackApiError as e:
                # This bot token may only have scope for one of public/private channels.
                if e.response.get("error") == "missing_scope":
                    break
                raise
            channels.extend(
                {"id": c["id"], "name": c["name"], "is_member": c.get("is_member", False)}
                for c in response["channels"]
                if c.get("is_member")
            )
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    return channels


@mcp.tool()
async def list_channel_messages(channel: Optional[str] = None, limit: int = 20) -> list[dict[str, Any]]:
    """
    Read recent messages from a Slack channel, newest first.

    Args:
        channel: Channel id (e.g. "C0123456789"). Defaults to the configured
            alerts channel if omitted. Call list_channels() first if unsure.
        limit: Max number of messages to return (default 20).
    """
    response = client.conversations_history(channel=channel or DEFAULT_CHANNEL, limit=limit)
    return [
        {"ts": m.get("ts"), "user": m.get("user"), "text": m.get("text", "")}
        for m in response["messages"]
    ]


@mcp.tool()
async def post_message(text: str, channel: Optional[str] = None, thread_ts: Optional[str] = None) -> dict[str, Any]:
    """
    Post a message to a Slack channel, optionally as a threaded reply.

    Args:
        text: Message text (markdown-ish Slack "mrkdwn" formatting is supported).
        channel: Channel id to post to. Defaults to the configured alerts channel if omitted.
        thread_ts: The `ts` of the parent message to reply in-thread to (from
            list_channel_messages or get_thread_replies). Omit to post a new top-level message.
    """
    response = client.chat_postMessage(channel=channel or DEFAULT_CHANNEL, text=text, thread_ts=thread_ts)
    return {"channel": response["channel"], "ts": response["ts"], "thread_ts": thread_ts}


@mcp.tool()
async def get_thread_replies(thread_ts: str, channel: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    """
    Read all replies in a thread, oldest first (the first item is the parent message itself).

    Args:
        thread_ts: The `ts` of the parent message that started the thread.
        channel: Channel id the thread is in. Defaults to the configured alerts channel if omitted.
        limit: Max number of replies to return (default 50).
    """
    response = client.conversations_replies(channel=channel or DEFAULT_CHANNEL, ts=thread_ts, limit=limit)
    return [
        {"ts": m.get("ts"), "user": m.get("user"), "text": m.get("text", "")}
        for m in response["messages"]
    ]


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
