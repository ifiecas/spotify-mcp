# app.py
import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route, Mount

# Load secrets (App Service will inject env vars; local dev uses .env)
load_dotenv()
CID = os.getenv("SPOTIFY_CLIENT_ID")
SEC = os.getenv("SPOTIFY_CLIENT_SECRET")
if not CID or not SEC:
    raise EnvironmentError("Missing SPOTIFY_CLIENT_ID/SECRET.")

# Import your existing tools by constructing the same FastMCP and defining tools
# You can either:
# 1) paste all @mcp.tool() functions here, or
# 2) import from server.py if you split tools into a module
mcp = FastMCP("spotify-mcp")

# ── paste all your @mcp.tool() functions from server.py below ──
# (identical definitions; do not include the mcp.run() block)
# ---------------------------------------------------------------

# Health for Azure probes
def healthz(request):
    return PlainTextResponse("ok")

# ✅ FastMCP ASGI app mounted at /mcp (method name may be `asgi_app()` in your version)
mcp_asgi = mcp.asgi_app(path="/mcp")

# Compose final Starlette app with both /healthz and /mcp
app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Mount("/mcp", app=mcp_asgi),
    ]
)
