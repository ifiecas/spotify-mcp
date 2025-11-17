from typing import Any, Dict, Optional
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request

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

# Create MCP server with dependencies
mcp = FastMCP("spotify-mcp", host="0.0.0.0", port=PORT, dependencies=[Request])

# ------------------------------------------------------
# HEADER VALIDATION – supports PowerApps / Copilot Studio
# ------------------------------------------------------
def validate_token(request: Request) -> bool:
    """
    Allows either:
      Authorization: Bearer XYZ
      api-key: Bearer XYZ
    """
    raw = None

    # Check Authorization header
    if "authorization" in request.headers:
        raw = request.headers["authorization"]
    # Check api-key header (alternative)
    elif "api-key" in request.headers:
        raw = request.headers["api-key"]

    if not raw:
        logger.warning("No authorization header found")
        logger.warning(f"Available headers: {list(request.headers.keys())}")
        return False

    if not raw.startswith("Bearer "):
        logger.warning(f"Invalid authorization format: {raw[:20]}...")
        return False

    token = raw.replace("Bearer ", "").strip()
    is_valid = token == LOCAL_TOKEN
    
    if not is_valid:
        logger.warning("Token validation failed")
    else:
        logger.info("Token validation successful")
    
    return is_valid


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
def search_artist_by_name(artist_name: str, request: Request) -> Any:
    """Search for artists on Spotify by name"""
    
    if not validate_token(request):
        logger.error("Unauthorized access attempt")
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
        logger.error(f"Search failed: {e}")
        return {"error": str(e)}


# ------------------------------------------------------
# TOOL: Get Top Tracks
# ------------------------------------------------------
@mcp.tool()
def get_artist_top_tracks(artist_id: str, request: Request) -> Any:
    """Get top tracks for a Spotify artist"""
    
    if not validate_token(request):
        logger.error("Unauthorized access attempt")
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
        logger.error(f"Get top tracks failed: {e}")
        return {"error": str(e)}


# ------------------------------------------------------
# TOOL: Get Albums
# ------------------------------------------------------
@mcp.tool()
def get_artist_albums(artist_id: str, request: Request) -> Any:
    """Get albums for a Spotify artist"""
    
    if not validate_token(request):
        logger.error("Unauthorized access attempt")
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
        logger.error(f"Get albums failed: {e}")
        return {"error": str(e)}


# ------------------------------------------------------
# RUN SERVER
# ------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"Spotify MCP Server running on port {PORT}")
    logger.info("Streaming MCP endpoints are available at /mcp")
    mcp.run(transport="streamable-http")
