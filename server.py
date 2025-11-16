from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv

# Official MCP library (this provides FastMCP internally)
from mcp.server import FastMCP
from mcp.server.middleware import Middleware, MiddlewareContext
from mcp.server.dependencies import get_http_headers
from mcp.errors import ToolError

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify Client ID/Secret")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

# Authentication Middleware for Copilot Studio
class UserAuthMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        api_key = headers.get("api-key")

        if not api_key:
            raise ToolError("Access denied: missing api key")

        if not api_key.startswith("Bearer "):
            raise ToolError("Access denied: invalid token format")

        token = api_key.replace("Bearer", "").strip()

        if token != LOCAL_TOKEN:
            raise ToolError("Access denied: invalid token")

        return await call_next(context)

# Detect Azure port
PORT = int(os.getenv("PORT", "8000"))

# Initialize MCP Server
mcp = FastMCP(
    "spotify-mcp",
    host="0.0.0.0",
    port=PORT
)

mcp.add_middleware(UserAuthMiddleware())

# Helper: Get Spotify API access token
def get_spotify_token() -> str:
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

# Tool 1: Search artist by name
@mcp.tool()
async def search_artist_by_name(artist_name: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Failed Spotify authentication"}

    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=5"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# Tool 2: Artist top tracks
@mcp.tool()
async def get_artist_top_tracks(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Failed Spotify authentication"}

    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=AU"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# Tool 3: Artist albums
@mcp.tool()
async def get_artist_albums(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Failed Spotify authentication"}

    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?market=AU&limit=10"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# Tool 4: Audio features for a track
@mcp.tool()
async def get_audio_features(track_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Failed Spotify authentication"}

    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# Tool 5: Artist audio profile (averaged metrics)
@mcp.tool()
async def get_artist_audio_profile(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Failed Spotify authentication"}

    headers = {"Authorization": f"Bearer {token}"}
    top_tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=AU"

    try:
        top_tracks_resp = requests.get(top_tracks_url, headers=headers)
        top_tracks_resp.raise_for_status()
        tracks = top_tracks_resp.json().get("tracks", [])

        if not tracks:
            return {"error": "No tracks found"}

        features = []
        for t in tracks:
            feat_url = f"https://api.spotify.com/v1/audio-features/{t['id']}"
            feat_resp = requests.get(feat_url, headers=headers)
            if feat_resp.status_code == 200:
                features.append(feat_resp.json())

        if not features:
            return {"error": "No audio features available"}

        averages = {}
        keys = ["danceability", "energy", "valence", "tempo"]
        for k in keys:
            vals = [f[k] for f in features if f.get(k) is not None]
            if vals:
                averages[k] = sum(vals) / len(vals)

        return averages

    except Exception as e:
        return {"error": str(e)}

# Run MCP Server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
