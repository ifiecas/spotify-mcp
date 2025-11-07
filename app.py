# app.py
import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing SPOTIFY_CLIENT_ID/SECRET.")

mcp = FastMCP("spotify-mcp")

# --- (your tools exactly as in server.py) ---
# paste all @mcp.tool() functions here unchanged
# --------------------------------------------

# ✅ Expose as an ASGI app that serves MCP over WebSocket at /mcp
# (Method name may vary by version; common ones are `asgi_app()` or `websocket_asgi()`)
app = mcp.asgi_app(path="/mcp")
