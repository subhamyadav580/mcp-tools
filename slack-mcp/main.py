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

    Call this first if you don't already know the channel id to use — the bot can only
    read/post in channels it has actually been invited to, so this is the full set of
    channels available to the other tools here.

    Returns:
        One entry per channel: {"id", "name", "is_member"}. `is_member` is always true
        here (channels the bot isn't in are filtered out). If the bot's token only has
        scope for one of public/private channels, that half is silently omitted rather
        than erroring — check the result against what you expected to see.
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
    Read recent top-level messages from a Slack channel, newest first.

    This only returns top-level channel messages — it does NOT include thread replies.
    Use get_thread_replies(ts) on a message's `ts` to read what's inside its thread.

    Args:
        channel: Channel id (e.g. "C0123456789"). Defaults to the configured alerts
            channel if omitted. Call list_channels() first if unsure which id to use.
        limit: Max number of messages to return (default 20).

    Returns:
        Messages as {"ts", "user", "text"}, newest first. `ts` is both the message's
        timestamp and its unique id — pass it as `thread_ts` to post_message or
        get_thread_replies to act on that specific message's thread.
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

    Prefer replying in-thread (pass thread_ts) when responding to a specific alert —
    it keeps the channel readable and keeps your response visibly tied to what
    triggered it, instead of adding an unrelated top-level message.

    Args:
        text: Message text. Slack "mrkdwn" formatting is supported: *bold*, _italic_,
            `code`, ```code block```, <https://url|link text>.
        channel: Channel id to post to. Defaults to the configured alerts channel if omitted.
        thread_ts: The `ts` of the parent message to reply in-thread to (from
            list_channel_messages or get_thread_replies). Omit to post a new top-level message.

    Returns:
        {"channel", "ts", "thread_ts"} — the posted message's own `ts` (usable as
        `thread_ts` for a further reply) and the `thread_ts` you passed in, if any.
    """
    response = client.chat_postMessage(channel=channel or DEFAULT_CHANNEL, text=text, thread_ts=thread_ts)
    return {"channel": response["channel"], "ts": response["ts"], "thread_ts": thread_ts}


@mcp.tool()
async def get_thread_replies(thread_ts: str, channel: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
    """
    Read a thread's full conversation, oldest first — the parent message plus every reply.

    Use this to check whether a human has already responded in a thread (e.g. on an
    alert) before posting your own reply into it.

    Args:
        thread_ts: The `ts` of the parent message that started the thread (from
            list_channel_messages, or a previous post_message call).
        channel: Channel id the thread is in. Defaults to the configured alerts channel if omitted.
        limit: Max number of messages to return, including the parent (default 50).

    Returns:
        Messages as {"ts", "user", "text"}, oldest first. The first item (index 0) is
        always the thread's parent message itself, not a reply.
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
