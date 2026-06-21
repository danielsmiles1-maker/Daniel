#!/usr/bin/env python3
"""
Confirm the Anthropic MCP connector reaches your MCP server end-to-end — WITHOUT the
voice loop. This calls Claude with the exact connector wiring jarvis.py uses, points it
at your tunnelled test server, and asks it to call two tools. If the secret word comes
back, the connector definitively works.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    export MCP_TEST_URL="https://<your-tunnel>.trycloudflare.com/mcp/"   # note the /mcp/ path
    # export MCP_TEST_TOKEN="..."   # only if you started the server with a token
    python test_connector.py
"""

import os
import sys

from anthropic import Anthropic

URL = os.getenv("MCP_TEST_URL")
TOKEN = os.getenv("MCP_TEST_TOKEN")  # optional; must match the server's token if set
MODEL = "claude-sonnet-4-6"
MCP_BETA = "mcp-client-2025-11-20"

if not os.getenv("ANTHROPIC_API_KEY"):
    sys.exit("Set ANTHROPIC_API_KEY first.")
if not URL:
    sys.exit('Set MCP_TEST_URL to your tunnel URL ending in /mcp/  '
             '(e.g. https://abc-def.trycloudflare.com/mcp/)')

server = {"type": "url", "url": URL, "name": "test-server"}
if TOKEN:
    server["authorization_token"] = TOKEN

client = Anthropic()
print(f"\n→ Asking Claude to use the connector at {URL}\n")

resp = client.beta.messages.create(
    model=MODEL,
    max_tokens=512,
    messages=[{
        "role": "user",
        "content": ("Use the test-server tools to do two things: "
                    "(1) call get_secret_word and tell me the secret word, and "
                    "(2) call add with a=20 and b=22 and tell me the result. "
                    "Report both plainly."),
    }],
    mcp_servers=[server],
    tools=[{"type": "mcp_toolset", "mcp_server_name": "test-server"}],
    betas=[MCP_BETA],
)

said = []
for b in resp.content:
    t = getattr(b, "type", None)
    if t == "mcp_tool_use":
        print(f"🔌 Claude called: {getattr(b, 'name', '?')}  args={getattr(b, 'input', {})}")
    elif t == "mcp_tool_result":
        content = getattr(b, "content", None)
        try:
            inner = content[0].text if content else ""
        except Exception:
            inner = str(content)
        print(f"   ↳ server returned: {inner}")
    elif t == "text":
        said.append(b.text)

final = " ".join(s.strip() for s in said if s.strip())
print("\nClaude:", final)

if "velvet-pangolin-8842" in final:
    print("\n✅ CONNECTOR CONFIRMED — the secret word came back through the connector.")
else:
    print("\n⚠️  Didn't see the secret word. Check: URL ends in /mcp/, the tunnel is up, "
          "and (if used) the token matches the server's.")
