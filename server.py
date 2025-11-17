from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.types import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

# Load environment
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN", "ivymcp")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure will assign PORT automatically
PORT = int(os.getenv("PORT", "8000"))

# -----------------------------
# Authentication Middleware
# -----------------------------
class AuthMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        api_key = headers.get("api-key")

        if not api_key or not api_key.startswith("Bearer "):
            raise ToolError("Access denied: missing or invalid api-key header")

        token = api_key.replace("Bearer ", "").strip()
        if token != LOCAL_TOKEN:
            raise ToolError("Access denied: invalid token")

        return await call_next(context)

# MCP Server
mcp = FastMCP("spotify-mcp", host="0.0.0.0", port=PORT)
mcp.add_middleware(AuthMiddleware())

# -----------------------------
# Spotify Token Helper
# -----------------------------
def get_spotify_token() -> str | None:
    url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    try:
        resp = requests.post(url, data=data, auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET), timeout=10)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

# -----------------------------
# MCP Tools
# -----------------------------
@mcp.tool()
def search_artist_by_name(artist_name: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = "https://api.spotify.com/v1/search"
    params = {"q": artist_name, "type": "artist", "limit": 5}
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_artist_top_tracks(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    params = {"market": "AU"}

    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_artist_albums(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {"market": "AU", "limit": 10}

    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# Run MCP Server
# -----------------------------
if __name__ == "__main__":
    logger.info(f"Starting Spotify MCP on 0.0.0.0:{PORT}")
    logger.info("Transport: streamable-http")
    logger.info("MCP endpoint: /mcp")
    mcp.run(transport="streamable-http")
