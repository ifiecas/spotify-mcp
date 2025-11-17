from typing import Any, Dict
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN", "ivymcp")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials")

PORT = int(os.getenv("PORT", "8000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

# Create MCP Server
mcp = FastMCP("spotify-mcp", host="0.0.0.0", port=PORT)


# ------------------------------------------------------
# HEADER VALIDATION (Fixes Copilot Studio Authorization)
# ------------------------------------------------------
def validate_token(headers: Dict[str, str]) -> bool:
    """
    Accepts both:
    Authorization: Bearer <token>
    api-key: Bearer <token>
    """

    token = None

    # Authorization header
    if "Authorization" in headers:
        raw = headers["Authorization"]
        if raw.startswith("Bearer "):
            token = raw.replace("Bearer ", "").strip()

    # api-key header (Power Apps / Copilot Studio)
    if not token and "api-key" in headers:
        raw = headers["api-key"]
        if raw.startswith("Bearer "):
            token = raw.replace("Bearer ", "").strip()

    # Validate final extracted token
    return token == LOCAL_TOKEN


# ------------------------------------------------------
# SPOTIFY TOKEN REQUEST
# ------------------------------------------------------
def get_spotify_token() -> str | None:
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
# TOOLS
# ------------------------------------------------------
@mcp.tool()
def search_artist_by_name(artist_name: str, headers: Dict[str, str] = None) -> Any:
    if not validate_token(headers or {}):
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


@mcp.tool()
def get_artist_top_tracks(artist_id: str, headers: Dict[str, str] = None) -> Any:
    if not validate_token(headers or {}):
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


@mcp.tool()
def get_artist_albums(artist_id: str, headers: Dict[str, str] = None) -> Any:
    if not validate_token(headers or {}):
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
    logger.info(f"Spotify MCP running on port {PORT}")
    logger.info("MCP endpoint available at /mcp")
    mcp.run(transport="streamable-http")
