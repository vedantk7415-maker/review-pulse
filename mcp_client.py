"""MCP publish client for Review Pulse.

Calls the n8n MCP Server Trigger tools (append_to_doc, create_email_draft)
over the Model Context Protocol (streamable HTTP transport).
Draft-only: create_email_draft never sends email.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
try:
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:  # newer mcp SDK renames the helper
    from mcp.client.streamable_http import streamable_http_client as streamablehttp_client

import analysis


def _snippet(result) -> str:
    parts = []
    for c in getattr(result, "content", []) or []:
        text = getattr(c, "text", None)
        if text:
            parts.append(str(text))
    return "; ".join(parts)[:500] or "no error detail"


async def _publish(mcp_url: str, text: str, subject: str, html: str) -> list[str]:
    steps: list[str] = []
    async with streamablehttp_client(mcp_url) as conn:
        read, write = conn[0], conn[1]
        async with ClientSession(read, write) as session:
            await session.initialize()
            r1 = await session.call_tool("append_to_doc", {"text": text})
            if getattr(r1, "isError", False):
                raise RuntimeError("append_to_doc failed: " + _snippet(r1))
            steps.append("append_to_doc → Google Doc appended")
            r2 = await session.call_tool(
                "create_email_draft", {"subject": subject, "html": html}
            )
            if getattr(r2, "isError", False):
                raise RuntimeError("create_email_draft failed: " + _snippet(r2))
            steps.append("create_email_draft → Gmail draft created (not sent)")
    return steps


def publish_via_mcp(mcp_url: str, payload: dict) -> list[str]:
    """Synchronous wrapper for Streamlit: calls both MCP tools in order."""
    return asyncio.run(
        _publish(
            mcp_url,
            payload["doc_entry"],
            payload["email_subject"],
            analysis.build_email_html(payload),
        )
    )


async def _check(mcp_url: str) -> list[str]:
    async with streamablehttp_client(mcp_url) as conn:
        read, write = conn[0], conn[1]
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            return [t.name for t in listed.tools]


def check_mcp(mcp_url: str) -> list[str]:
    """Handshake + tools/list (read-only, no side effects). Returns tool names."""
    return asyncio.run(_check(mcp_url))
