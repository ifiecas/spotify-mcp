from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv

from fastmcp.server import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.errors import ToolError

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
API_TOKEN = os.getenv("API_TOKEN")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

# AUTH MIDDLEWARE
class UserAuthMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):

        headers = get_http_headers()
        api_key = headers.get("api-key")

        if not api_key:
            raise ToolError("Access denied: no key provided")

        if not api_key.startswith("Bearer "):
            raise ToolError("Access denied: invalid token format")

        token = api_key.removeprefix("Bearer ").strip()

        if token != LOCAL_TOKEN:
            raise ToolError("Access denied: invalid token")

        return await call_next(context)

# MCP SERVER
PORT = int(os.getenv("PORT", "8000"))

mcp = FastMCP(
    "spotify-mcp",
    host="0.0.0.0",
    port=PORT
)

mcp.add_middleware(UserAuthMiddleware())

# Spotify token fetch
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    try:
        resp = requests.post(url, data=data, auth=auth)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

# TOOL: search artist
@mcp.tool()
async def search_artist_by_name(artist_name: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=5"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# TOOL: top tracks
@mcp.tool()
async def get_artist_top_tracks(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=AU"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# TOOL: albums
@mcp.tool()
async def get_artist_albums(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?market=AU&limit=10"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# TOOL: audio features
@mcp.tool()
async def get_audio_features(track_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# TOOL: audio profile
@mcp.tool()
async def get_artist_audio_profile(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    headers = {"Authorization": f"Bearer {token}"}
    top_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=AU"

    try:
        resp = requests.get(top_url, headers=headers)
        resp.raise_for_status()
        tracks = resp.json().get("tracks", [])

        if not tracks:
            return {"error": "No tracks found"}

        features = []
        for t in tracks:
            f_url = f"https://api.spotify.com/v1/audio-features/{t['id']}"
            fr = requests.get(f_url, headers=headers)
            if fr.status_code == 200:
                features.append(fr.json())

        if not features:
            return {"error": "No audio features"}

        avg = {}
        for key in ["danceability", "energy", "valence", "tempo"]:
            vals = [f[key] for f in features if f.get(key) is not None]
            if vals:
                avg[key] = sum(vals) / len(vals)

        return avg

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
