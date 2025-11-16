from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv

from mcp.server import FastMCP
from mcp.server.models import ToolError
from mcp.server.hooks import register_request_hook

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials")

PORT = int(os.getenv("PORT", "8000"))

mcp = FastMCP(
    "spotify-mcp",
    host="0.0.0.0",
    port=PORT
)

# Authentication hook
@register_request_hook
def check_auth(request, headers):
    api_key = headers.get("api-key")

    if not api_key:
        raise ToolError(message="Access denied: missing api key")

    if not api_key.startswith("Bearer "):
        raise ToolError(message="Access denied: invalid token format")

    token = api_key.replace("Bearer", "").strip()

    if token != LOCAL_TOKEN:
        raise ToolError(message="Access denied: invalid token")

# Get Spotify token
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

# Tool 1 search artists
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

# Tool 2 top tracks
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

# Tool 3 albums
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

# Tool 4 track audio features
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

# Tool 5 artist audio profile
@mcp.tool()
async def get_artist_audio_profile(artist_id: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    headers = {"Authorization": f"Bearer {token}"}
    top_tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=AU"

    try:
        resp = requests.get(top_tracks_url, headers=headers)
        resp.raise_for_status()
        tracks = resp.json().get("tracks", [])

        if not tracks:
            return {"error": "No tracks found"}

        features = []
        for t in tracks:
            feat_url = f"https://api.spotify.com/v1/audio-features/{t['id']}"
            fr = requests.get(feat_url, headers=headers)
            if fr.status_code == 200:
                features.append(fr.json())

        if not features:
            return {"error": "No audio features"}

        averages = {}
        keys = ["danceability", "energy", "valence", "tempo"]

        for k in keys:
            vals = [f[k] for f in features if f.get(k) is not None]
            if vals:
                averages[k] = sum(vals) / len(vals)

        return averages

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
