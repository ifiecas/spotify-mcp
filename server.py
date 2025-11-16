from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials in environment")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure will set PORT, default to 8000 for local
PORT = int(os.getenv("PORT", "8000"))

# FastMCP server
mcp = FastMCP("spotify-mcp")

# Helper: get Spotify auth token
def get_spotify_token() -> str | None:
    url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    try:
        resp = requests.post(url, data=data, auth=auth, timeout=10)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            logger.error("No access_token in Spotify response")
        return token
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

# Tool 1 - search artist
@mcp.tool()
def search_artist_by_name(artist_name: str) -> Any:
    """
    Search Spotify for an artist by name.
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Could not authenticate with Spotify"}
    
    url = "https://api.spotify.com/v1/search"
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 5,
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify search error: {e}")
        return {"error": str(e)}

# Tool 2 - top tracks
@mcp.tool()
def get_artist_top_tracks(artist_id: str) -> Any:
    """
    Get an artist's top tracks in AU market.
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}
    
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    params = {"market": "AU"}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify top tracks error: {e}")
        return {"error": str(e)}

# Tool 3 - artist albums
@mcp.tool()
def get_artist_albums(artist_id: str) -> Any:
    """
    Get an artist's albums.
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}
    
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {
        "market": "AU",
        "limit": 10,
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify albums error: {e}")
        return {"error": str(e)}

# Run Streamable HTTP server
if __name__ == "__main__":
    # Run with streamable-http transport
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=PORT
    )
