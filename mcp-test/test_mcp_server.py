#!/usr/bin/env python3
"""
A tiny MCP server, purely to confirm the Anthropic MCP connector works end-to-end
BEFORE you wrestle with Google OAuth. Three trivial tools — including a "secret word"
that Claude could not possibly know unless it actually called this server.

WHY A TUNNEL?  Anthropic's connector calls your server from Anthropic's side, over the
internet. A server on localhost is not reachable from there. So you run this locally and
expose it with one command (see CONNECTOR_TEST.md). That's the same shape you'll use for
Google — just without the OAuth.

Install:
    pip install fastmcp

Run (no auth — simplest):
    python test_mcp_server.py

Run (with a bearer token — rehearses the authenticated path Google will need):
    export MCP_TEST_TOKEN="supersecret-test-token-123"
    python test_mcp_server.py

Then expose port 8000 with a tunnel and point the connector at <tunnel-url>/mcp/
(see CONNECTOR_TEST.md). Default endpoint path is /mcp/.
"""

import os
import datetime

from fastmcp import FastMCP

TOKEN = os.getenv("MCP_TEST_TOKEN")  # optional: set to require a bearer token

auth = None
if TOKEN:
    # StaticTokenVerifier is FastMCP's built-in "API-key style" verifier for dev/testing.
    # Each token's claims MUST include "client_id" (the verifier reads it).
    from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
    auth = StaticTokenVerifier(tokens={TOKEN: {"client_id": "jarvis-test", "scope": "read"}})

mcp = FastMCP(name="jarvis-test-server", auth=auth)


@mcp.tool
def get_secret_word() -> str:
    """Return the secret word. The only way to know it is to call this tool —
    so if Claude can say it, the connector definitely reached this server."""
    return "velvet-pangolin-8842"


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers and return their sum."""
    return a + b


@mcp.tool
def get_server_time() -> str:
    """Return the current date and time on the machine running this MCP server."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


if __name__ == "__main__":
    port = int(os.getenv("MCP_TEST_PORT", "8000"))
    print(f"\n  jarvis-test-server  →  http://127.0.0.1:{port}/mcp/")
    print(f"  auth: {'bearer token required' if TOKEN else 'none (open)'}")
    print(f"  tools: get_secret_word, add, get_server_time\n")
    mcp.run(transport="http", host="127.0.0.1", port=port)
