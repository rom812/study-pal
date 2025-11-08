"""Connectors wrapping Model Context Protocol clients."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import timedelta

import anyio
import mcp
from mcp import types
from mcp.client.session_group import ClientSessionGroup, StreamableHttpParameters
from mcp.shared.exceptions import McpError

logger = logging.getLogger(__name__)


@dataclass
class CalendarConnector:
    """Thin wrapper around the calendar MCP capability."""

    endpoint: str | None = None
    auth_token: str | None = None
    create_event_tool: str = "create-event"
    request_timeout_seconds: float = 30.0
    sse_read_timeout_seconds: float = 300.0

    _resolved_tool_name: str | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.endpoint is None:
            self.endpoint = (
                os.getenv("GOOGLE_CALENDAR_MCP_URL")
                or os.getenv("GOOGLE_CALENDAR_MCP_HTTP_URL")
                or os.getenv("GOOGLE_CALENDAR_MCP_ENDPOINT")
            )
        if self.auth_token is None:
            self.auth_token = os.getenv("GOOGLE_CALENDAR_MCP_TOKEN")
        tool_override = os.getenv("GOOGLE_CALENDAR_MCP_CREATE_TOOL")
        if tool_override:
            self.create_event_tool = tool_override

    def create_event(self, payload: dict) -> None:
        if not isinstance(payload, dict):
            raise TypeError("Calendar payload must be provided as a dictionary.")

        # Check if calendar is configured before attempting to create event
        if not self.endpoint:
            logger.info(
                "Google Calendar MCP endpoint is not configured. "
                "Event creation skipped. To enable calendar sync, set GOOGLE_CALENDAR_MCP_URL environment variable."
            )
            print("ℹ️  Calendar sync skipped (no MCP endpoint configured)")
            return

        anyio.run(self._create_event_async, payload)

    async def _create_event_async(self, payload: dict) -> None:
        server_params = self._build_server_parameters()
        try:
            async with ClientSessionGroup() as group:
                session = await group.connect_to_server(server_params)
                tool_name = await self._resolve_tool_name(session)
                result = await session.call_tool(tool_name, payload)
        except McpError as exc:
            raise RuntimeError(f"Google Calendar MCP interaction failed: {exc}") from exc
        except Exception as exc:
            # Handle connection errors gracefully
            logger.warning(f"Failed to connect to calendar MCP server: {exc}")
            print(f"⚠️  Calendar sync failed: Could not connect to MCP server at {self.endpoint}")
            return

        if result.isError:
            message = self._summarize_error(result)
            raise RuntimeError(f"Google Calendar MCP reported an error: {message}")

        logger.debug(
            "Created calendar event via MCP tool %s (structured=%s, content=%s)",
            self._resolved_tool_name,
            result.structuredContent,
            result.content,
        )

    def _build_server_parameters(self) -> StreamableHttpParameters:
        endpoint = self._resolve_endpoint()
        headers = self._build_headers()
        return StreamableHttpParameters(
            url=endpoint,
            headers=headers if headers else None,
            timeout=timedelta(seconds=self.request_timeout_seconds),
            sse_read_timeout=timedelta(seconds=self.sse_read_timeout_seconds),
        )

    def _resolve_endpoint(self) -> str:
        if not self.endpoint:
            raise RuntimeError(
                "Google Calendar MCP endpoint is not configured. "
                "Set GOOGLE_CALENDAR_MCP_URL or provide endpoint explicitly."
            )
        return self.endpoint

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def _resolve_tool_name(self, session: mcp.ClientSession) -> str:
        if self._resolved_tool_name:
            return self._resolved_tool_name

        try:
            tools_result = await session.list_tools()
        except McpError as exc:
            raise RuntimeError("Unable to list tools from Google Calendar MCP server.") from exc

        tool_names = [tool.name for tool in tools_result.tools]

        if self.create_event_tool in tool_names:
            self._resolved_tool_name = self.create_event_tool
            return self._resolved_tool_name

        fallback = next(
            (name for name in tool_names if "create" in name and "calendar" in name),
            None,
        )

        if fallback:
            self._resolved_tool_name = fallback
            logger.debug("Resolved calendar create-event tool name to %s", fallback)
            return fallback

        available = ", ".join(tool_names) or "<none>"
        raise RuntimeError(
            f"No calendar create-event tool available on MCP server. Available tools: {available}"
        )

    @staticmethod
    def _summarize_error(result: types.CallToolResult) -> str:
        if result.structuredContent:
            message = result.structuredContent.get("message")
            if message:
                return str(message)

        text_chunks = []
        for chunk in result.content:
            if hasattr(chunk, "text") and chunk.text:
                text_chunks.append(chunk.text)

        return " ".join(text_chunks).strip() or "Unknown error from MCP tool."

    def update_event(self, event_id: str, payload: dict) -> None:
        # TODO: update events via MCP
        _ = (event_id, payload)


@dataclass
class MailConnector:
    """Handles outbound email reminders through MCP."""

    def send_email(self, payload: dict) -> None:
        # TODO: send emails via Gmail MCP connector
        _ = payload
