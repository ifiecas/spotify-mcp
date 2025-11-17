from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.errors import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

# Load environment vars
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN", "ivymcp")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "8000"))

# Authentication middleware
class AuthMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        api_key = headers.get("api-key")

        if not api_key or not api_key.startswith("Bearer "):
            raise ToolError("Access denied: missing or invalid token")

        token = api_key.replace("Bearer ", "").strip()

        if token != LOCAL_TOKEN:
            raise ToolError("Access denied: invalid token")

        return await call_next(context)

# Create the MCP server
mcp = FastMCP("spotify-mcp", host="0.0.0.0", port=PORT)
mcp.add_middleware(AuthMiddleware())

# Spotify auth helper
def get_spotify_token() -> str | None:
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

# Tools
@mcp.tool()
def search_artist_by_name(artist_name: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            params={"q": artist_name, "type": "artist", "limit": 5},
            headers={"Authorization": f"Bearer {token}"}
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_artist_top_tracks(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
            params={"market": "AU"},
            headers={"Authorization": f"Bearer {token}"}
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_artist_albums(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/albums",
            params={"market": "AU", "limit": 10},
            headers={"Authorization": f"Bearer {token}"}
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# Run server
if __name__ == "__main__":
    logger.info(f"Starting Spotify MCP server on port {PORT}")
    logger.info("Endpoint: /mcp")
    mcp.run(transport="streamable-http")
