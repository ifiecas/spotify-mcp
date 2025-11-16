from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.middleware import Middleware, MiddlewareContext
from mcp.server.dependencies import get_http_headers
from mcp.server.models import ToolError

# Load environment variables from .env (for local dev)
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")  # your Copilot token

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

# ──────────────────────────
# Authentication middleware
# ──────────────────────────

class UserAuthMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        api_key = headers.get("api-key")

        if not api_key:
            raise ToolError(code="unauthorized", message="Access denied: missing api key")

        if not api_key.startswith("Bearer "):
            raise ToolError(code="unauthorized", message="Access denied: invalid token format")

        token = api_key.removeprefix("Bearer ").strip()

        if token != LOCAL_TOKEN:
            raise ToolError(code="unauthorized", message="Access denied: invalid token")

        return await call_next(context)

# ──────────────────────────
# MCP server init
# ──────────────────────────

PORT = int(os.getenv("PORT", "8000"))

mcp = Server(
    "spotify-mcp",
    host="0.0.0.0",
    port=PORT,
)

mcp.add_middleware(UserAuthMiddleware())

# ──────────────────────────
# Spotify helpers
# ──────────────────────────

def get_spotify_token() -> str | None:
    url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    try:
        resp = requests.post(url, data=data, auth=auth, timeout=10)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            logger.error("Spotify token missing in response")
        return token
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

def spotify_get(url: str) -> Any:
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify API error for {url}: {e}")
        return {"error": str(e)}

# ──────────────────────────
# MCP tools
# ──────────────────────────

@mcp.tool()
async def search_artist_by_name(artist_name: str) -> Any:
    """
    Search Spotify for artists by name.
    """
    q = artist_name.strip()
    url = f"https://api.spotify.com/v1/search?q={q}&type=artist&limit=5"
    return spotify_get(url)

@mcp.tool()
async def get_artist_top_tracks(artist_id: str, market: str = "AU") -> Any:
    """
    Get an artist's top tracks in a given market.
    """
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market={market}"
    return spotify_get(url)

@mcp.tool()
async def get_artist_albums(artist_id: str, market: str = "AU", limit: int = 10) -> Any:
    """
    Get an artist's albums.
    """
    url = (
        f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        f"?market={market}&limit={limit}"
    )
    return spotify_get(url)

@mcp.tool()
async def get_audio_features(track_id: str) -> Any:
    """
    Get audio features for a single track.
    """
    url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    return spotify_get(url)

@mcp.tool()
async def get_artist_audio_profile(artist_id: str, market: str = "AU") -> Any:
    """
    Compute an average audio profile from the artist's top tracks.
    Returns average danceability, energy, valence and tempo.
    """
    top_tracks = spotify_get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market={market}"
    )
    if isinstance(top_tracks, dict) and top_tracks.get("error"):
        return top_tracks

    tracks = top_tracks.get("tracks", [])
    if not tracks:
        return {"error": "No tracks found for artist"}

    features = []
    for t in tracks:
        tid = t.get("id")
        if not tid:
            continue
        feat = spotify_get(f"https://api.spotify.com/v1/audio-features/{tid}")
        if isinstance(feat, dict) and feat.get("id"):
            features.append(feat)

    if not features:
        return {"error": "Could not load audio features"}

    keys = ["danceability", "energy", "valence", "tempo"]
    averages: dict[str, float] = {}

    for k in keys:
        vals = [f[k] for f in features if f.get(k) is not None]
        if vals:
            averages[k] = sum(vals) / len(vals)

    return {
        "artist_id": artist_id,
        "track_count": len(features),
        "averages": averages,
    }

# ──────────────────────────
# Entry point
# ──────────────────────────

if __name__ == "__main__":
    logger.info(f"Starting Spotify MCP on 0.0.0.0:{PORT}")
    mcp.run(transport="streamable-http")
