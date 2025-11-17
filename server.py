from typing import Any, Dict, Optional
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")  # must be supplied by Azure

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials (CLIENT ID + SECRET)")

if not LOCAL_TOKEN:
    raise EnvironmentError("Missing LOCAL_TOKEN env variable")

PORT = int(os.getenv("PORT", "8000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

# Create MCP server
mcp = FastMCP("spotify-mcp", host="0.0.0.0", port=PORT)

# ------------------------------------------------------
# HEADER VALIDATION – supports PowerApps / Copilot Studio
# ------------------------------------------------------
def validate_token(headers: Dict[str, str]) -> bool:
    """
    Allows either:
      Authorization: Bearer XYZ
      api-key: Bearer XYZ
    """
    raw = None

    if headers.get("Authorization"):
        raw = headers["Authorization"]

    elif headers.get("api-key"):
        raw = headers["api-key"]

    if not raw:
        return False

    if not raw.startswith("Bearer "):
        return False

    token = raw.replace("Bearer ", "").strip()
    return token == LOCAL_TOKEN


# ------------------------------------------------------
# SPOTIFY CLIENT CREDENTIALS TOKEN
# ------------------------------------------------------
def get_spotify_token() -> Optional[str]:
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error(f"Spotify authentication failed: {e}")
        return None


# ------------------------------------------------------
# TOOL: Search Artist
# ------------------------------------------------------
@mcp.tool()
def search_artist_by_name(artist_name: str, headers: Dict[str, str] = None) -> Any:
    headers = headers or {}

    if not validate_token(headers):
        return {"error": "Unauthorized"}

    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            params={"q": artist_name, "type": "artist", "limit": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ------------------------------------------------------
# TOOL: Get Top Tracks
# ------------------------------------------------------
@mcp.tool()
def get_artist_top_tracks(artist_id: str, headers: Dict[str, str] = None) -> Any:
    headers = headers or {}

    if not validate_token(headers):
        return {"error": "Unauthorized"}

    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
            params={"market": "AU"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ------------------------------------------------------
# TOOL: Get Albums
# ------------------------------------------------------
@mcp.tool()
def get_artist_albums(artist_id: str, headers: Dict[str, str] = None) -> Any:
    headers = headers or {}

    if not validate_token(headers):
        return {"error": "Unauthorized"}

    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/albums",
            params={"market": "AU", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ------------------------------------------------------
# RUN SERVER
# ------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"Spotify MCP Server running on port {PORT}")
    logger.info("Streaming MCP endpoints are available at /mcp")
    mcp.run(transport="streamable-http")
