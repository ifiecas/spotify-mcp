"""
Spotify MCP Server 🎧
=====================
Author: Ivy Fiecas-Borjal

A Model Context Protocol (MCP) server that connects to the Spotify Web API.
Compatible with Microsoft Copilot Studio via the mcp-streamable-1.0 protocol.

Tools:
  🎵 search_artist_by_name
  🔝 get_artist_top_tracks
  💿 get_artist_albums
  🎚️ get_audio_features
  🎼 get_artist_profile
"""

import os
import time
import requests
import logging
import uvicorn
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastapi import Request
from starlette.responses import PlainTextResponse, JSONResponse
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# ⚙️ Environment Setup
# ─────────────────────────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("❌ Missing Spotify credentials. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to your .env file or Azure App Settings.")

# ─────────────────────────────────────────────
# 🔧 Logging
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ─────────────────────────────────────────────
# 🧠 MCP Initialization
# ─────────────────────────────────────────────
mcp = FastMCP("🎧 Spotify MCP", stateless_http=True)
app = mcp.streamable_http_app()
app.debug = False

# ─────────────────────────────────────────────
# 🔐 Token Cache
# ─────────────────────────────────────────────
_cached_token = None
_token_expiry = 0

def get_spotify_token() -> str:
    """Fetch Spotify API token and cache until expiry."""
    global _cached_token, _token_expiry
    now = time.time()

    if _cached_token and now < _token_expiry:
        return _cached_token

    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10,
    )
    res.raise_for_status()
    data = res.json()
    _cached_token = data["access_token"]
    _token_expiry = now + data.get("expires_in", 3600) - 30
    return _cached_token

# ─────────────────────────────────────────────
# 🎵 Tool 1: Search Artist by Name
# ─────────────────────────────────────────────
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": artist_name, "type": "artist", "limit": limit}
    res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json().get("artists", {}).get("items", [])
    return [
        {
            "id": a["id"],
            "name": a["name"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
            "url": a["external_urls"]["spotify"],
        }
        for a in data
    ]

# ─────────────────────────────────────────────
# 🔝 Tool 2: Get Artist Top Tracks
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US") -> List[Dict[str, Any]]:
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    res = requests.get(url, headers=headers, params={"market": market}, timeout=10)
    res.raise_for_status()
    tracks = res.json().get("tracks", [])
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "album": t["album"]["name"],
            "popularity": t["popularity"],
            "url": t["external_urls"]["spotify"],
        }
        for t in tracks
    ]

# ─────────────────────────────────────────────
# 💿 Tool 3: Get Artist Albums
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_albums(artist_id: str, include_tracks: bool = False) -> List[Dict[str, Any]]:
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"include_groups": "album,single", "market": "US", "limit": 20}
    res = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}/albums", headers=headers, params=params, timeout=10)
    res.raise_for_status()
    albums_data = res.json().get("items", [])
    albums = []
    for a in albums_data:
        album = {
            "id": a["id"],
            "name": a["name"],
            "release_date": a["release_date"],
            "total_tracks": a["total_tracks"],
            "url": a["external_urls"]["spotify"],
        }
        if include_tracks:
            tr_res = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers, timeout=10)
            tr_res.raise_for_status()
            album["tracks"] = [t["name"] for t in tr_res.json().get("items", [])]
        albums.append(album)
    return albums

# ─────────────────────────────────────────────
# 🎚️ Tool 4: Get Audio Features
# ─────────────────────────────────────────────
@mcp.tool()
def get_audio_features(track_ids: List[str]) -> List[Dict[str, Any]]:
    if not track_ids:
        return [{"error": "No track IDs provided."}]
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.spotify.com/v1/audio-features",
        headers=headers,
        params={"ids": ",".join(track_ids[:100])},
        timeout=10,
    )
    res.raise_for_status()
    data = res.json().get("audio_features", [])
    return [
        {
            "id": f["id"],
            "danceability": f["danceability"],
            "energy": f["energy"],
            "valence": f["valence"],
            "tempo": f["tempo"],
        }
        for f in data if f
    ]

# ─────────────────────────────────────────────
# 🎼 Tool 5: Artist Profile Summary
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_profile(artist_id: str) -> Dict[str, Any]]:
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    albums_res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 20, "market": "US"},
        timeout=10,
    )
    albums_res.raise_for_status()
    albums = albums_res.json().get("items", [])
    track_ids = []
    for a in albums:
        tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers, timeout=10)
        tr.raise_for_status()
        track_ids.extend([t["id"] for t in tr.json().get("items", [])])
    if not track_ids:
        return {"message": "No tracks found for this artist."}
    features_res = requests.get(
        "https://api.spotify.com/v1/audio-features",
        headers=headers,
        params={"ids": ",".join(track_ids[:100])},
        timeout=10,
    )
    features_res.raise_for_status()
    features = [f for f in features_res.json().get("audio_features", []) if f]

    def avg(key):
        vals = [f[key] for f in features if f.get(key)]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    return {
        "artist_id": artist_id,
        "summary": {
            "avg_danceability": avg("danceability"),
            "avg_energy": avg("energy"),
            "avg_valence": avg("valence"),
            "avg_tempo": avg("tempo"),
        },
        "sample_tracks": len(features),
    }

# ─────────────────────────────────────────────
# 🌐 MCP Streamable Endpoint (for Copilot)
# ─────────────────────────────────────────────
@app.post("/mcp")
async def invoke_mcp(request: Request):
    """Handle MCP requests from Copilot Studio."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    tool = body.get("tool")
    args = body.get("args", {})

    mapping = {
        "search_artist_by_name": search_artist_by_name,
        "get_artist_top_tracks": get_artist_top_tracks,
        "get_artist_albums": get_artist_albums,
        "get_audio_features": get_audio_features,
        "get_artist_profile": get_artist_profile,
    }

    if tool not in mapping:
        return JSONResponse(
            {"error": f"Unknown tool '{tool}'", "available_tools": list(mapping.keys())},
            status_code=400,
        )

    try:
        result = mapping[tool](**args)
        return JSONResponse(result)
    except Exception as e:
        logging.exception("Error in MCP tool call")
        return JSONResponse({"error": str(e)}, status_code=500)

# ─────────────────────────────────────────────
# 🩺 Health Check
# ─────────────────────────────────────────────
@app.get("/")
async def root():
    return PlainTextResponse("🎧 Spotify MCP Server is alive and streamable via /mcp")

# ─────────────────────────────────────────────
# 🚀 Run the MCP Server
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logging.info("Starting Spotify MCP server on http://localhost:3000 → /mcp")
    uvicorn.run("server:app", host="0.0.0.0", port=3000)
