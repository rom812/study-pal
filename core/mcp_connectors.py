"""Connectors wrapping Model Context Protocol clients."""

from __future__ import annotations

import asyncio
import logging
import os
import warnings
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

        # Temporarily suppress unhandled exception warnings during asyncio.run() shutdown
        # These occur when anyio cancel scopes are cleaned up in different tasks
        loop = None
        old_exception_handler = None

        def suppress_cancel_scope_errors(loop, context):
            """Suppress 'cancel scope in different task' errors during MCP client shutdown."""
            exception = context.get("exception")
            if isinstance(exception, RuntimeError) and "cancel scope" in str(exception).lower():
                # Suppress this specific error - it's a cleanup issue in the MCP client library
                logger.debug("Suppressed anyio cancel scope cleanup error during MCP shutdown")
                return
            # For other exceptions, use the default handler
            if old_exception_handler:
                old_exception_handler(loop, context)
            else:
                loop.default_exception_handler(context)

        try:
            # Create a new event loop for this async operation
            loop = asyncio.new_event_loop()
            old_exception_handler = loop.get_exception_handler()
            loop.set_exception_handler(suppress_cancel_scope_errors)
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(self._create_event_async(payload))
            finally:
                # Clean up the event loop
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except Exception:
                    pass
                loop.close()
                asyncio.set_event_loop(None)
        except asyncio.CancelledError as exc:
            logger.warning("Calendar MCP interaction cancelled: %s", exc)
            print("⚠️  Calendar sync failed: MCP request cancelled")
        except RuntimeError as exc:
            # Catch anyio cancel scope errors during cleanup
            if "cancel scope" in str(exc).lower():
                logger.debug("Suppressed anyio cancel scope cleanup error: %s", exc)
            else:
                logger.warning("Calendar sync runtime error: %s", exc)
                print(f"⚠️  Calendar sync failed: {type(exc).__name__}")
        except Exception as exc:
            # Handle any connection or runtime errors gracefully
            logger.warning("Failed to create calendar event: %s", exc)
            print(f"⚠️  Calendar sync failed: {type(exc).__name__}")
            # Don't raise - allow the system to continue

    async def _create_event_async(self, payload: dict) -> None:
        server_params = self._build_server_parameters()
        session_group = None
        try:
            session_group = ClientSessionGroup()
            async with session_group:
                session = await session_group.connect_to_server(server_params)
                tool_name = await self._resolve_tool_name(session)
                result = await session.call_tool(tool_name, payload)

                if result.isError:
                    message = self._summarize_error(result)
                    raise RuntimeError(f"Google Calendar MCP reported an error: {message}")

                logger.debug(
                    "Created calendar event via MCP tool %s (structured=%s, content=%s)",
                    self._resolved_tool_name,
                    result.structuredContent,
                    result.content,
                )
        except asyncio.CancelledError:
            logger.info("Calendar MCP connection cancelled")
            print(f"⚠️  Calendar sync cancelled while contacting {self.endpoint}")
            # Suppress the cancellation - don't re-raise to avoid cleanup errors
            return
        except McpError as exc:
            raise RuntimeError(f"Google Calendar MCP interaction failed: {exc}") from exc
        except Exception as exc:
            # Handle connection errors gracefully
            logger.warning(f"Failed to connect to calendar MCP server: {exc}")
            print(f"⚠️  Calendar sync failed: Could not connect to MCP server at {self.endpoint}")
            return

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
