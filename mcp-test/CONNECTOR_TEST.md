# Confirming the MCP connector end-to-end

Goal: prove Jarvis's MCP connector actually reaches a remote MCP server and runs its tools — **before** you wrestle with Google OAuth. About 10 minutes. When this works, Google is just swapping this throwaway server for Google's, with a real OAuth token instead of a test one. The Jarvis side doesn't change.

## Why a tunnel is needed

Anthropic's connector calls your MCP server **from Anthropic's servers, over the internet** — not from your machine. So a server bound to `localhost` is unreachable (Claude would be hitting *its own* localhost). We run the test server locally and expose it briefly with a tunnel. That's the whole reason for step 2.

---

## Steps

### 1 — Run the test server

```bash
pip install fastmcp anthropic
python test_mcp_server.py
```

It serves at `http://127.0.0.1:8000/mcp/` with three tools: `get_secret_word`, `add`, `get_server_time`. Leave it running.

### 2 — Expose it with a tunnel (pick one)

**Cloudflare (no signup, easiest):**
```bash
# install once: brew install cloudflared   (or download from Cloudflare)
cloudflared tunnel --url http://localhost:8000
```
Copy the `https://….trycloudflare.com` URL it prints.

**ngrok (needs a free account):**
```bash
ngrok http 8000
```
Copy the `https://….ngrok-free.app` forwarding URL.

### 3 — Run the connector test

Your connector URL = **tunnel URL + `/mcp/`** (mind the path and trailing slash):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export MCP_TEST_URL="https://your-tunnel.trycloudflare.com/mcp/"
python test_connector.py
```

Expected:
```
🔌 Claude called: get_secret_word  args={}
🔌 Claude called: add  args={'a': 20, 'b': 22}
Claude: The secret word is velvet-pangolin-8842, and 20 + 22 = 42.

✅ CONNECTOR CONFIRMED
```

If you see `velvet-pangolin-8842`, the connector works end-to-end — Claude could not have known that word any other way.

### 4 — (Optional) rehearse the authenticated path

Google's connector will require a token, so prove that path too. Restart the server with a token:

```bash
# terminal A
export MCP_TEST_TOKEN="supersecret-test-token-123"
python test_mcp_server.py

# terminal B  (re-tunnel if needed, then)
export MCP_TEST_URL="https://your-tunnel.trycloudflare.com/mcp/"
export MCP_TEST_TOKEN="supersecret-test-token-123"   # must match the server
python test_connector.py
```

The token is passed exactly the way `jarvis.py` passes connector tokens (`authorization_token`). Verified locally: no token → rejected, correct token → works, wrong token → rejected.

### 5 — Wire it into Jarvis

In `jarvis.py`, add the tunnel as an MCP server:

```python
MCP_SERVERS = [
    {"name": "test-server", "url": "https://your-tunnel.trycloudflare.com/mcp/", "token_env": "MCP_TEST_TOKEN"},
]
```

Set `MCP_TEST_TOKEN` in `.env` (or drop `token_env` for the open server), restart Jarvis, open `http://localhost:4444`, and ask by voice: **"What's the secret word?"** Jarvis calls the connector and speaks `velvet-pangolin-8842` back — you'll see `🔌 test-server: get_secret_word` in the transcript. The entire path is now proven.

---

## Notes

- `trycloudflare.com` URLs are **ephemeral** — a new one each run. Fine for testing; for anything lasting, use a named Cloudflare tunnel or deploy the server.
- Default endpoint path is `/mcp/`. The connector URL must include it.
- `fastmcp` is only needed for this test server, not for `jarvis.py` itself.
- Next: replace `test-server` with a real connector. Google's MCP endpoints need a Google OAuth access token carrying the right scopes — that's the OAuth setup this test let you skip for now.
