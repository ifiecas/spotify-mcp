"""
Spotify MCP Server 🎧
=====================
Author: Ivy Fiecas-Borjal

A Model Context Protocol (MCP) server that connects to the Spotify Web API
and exposes tools for Microsoft Copilot Studio via mcp-streamable-1.0.

Features:
    🎵 search_artist_by_name
    🔝 get_artist_top_tracks
    💿 get_artist_albums
"""

import os
import logging
import multiprocessing
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# ───────────────────────────
# 🔧 Setup
# ───────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("❌ Missing Spotify credentials in .env")

# Initialize FastMCP + FastAPI app
mcp = FastMCP("spotify-mcp", stateless_http=True)
app = mcp.streamable_http_app()

# Enable CORS (✅ fixes “Failed to fetch” in Swagger/Copilot)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can later restrict this to Copilot Studio origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# ───────────────────────────
# 🔐 Spotify Token Helper
# ───────────────────────────
def get_spotify_token() -> str:
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10,
    )
    res.raise_for_status()
    return res.json()["access_token"]

# ───────────────────────────
# 🎵 MCP Tools
# ───────────────────────────
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5):
    """Search for artists by name and return their Spotify IDs."""
    token = get_spotify_token()
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": artist_name, "type": "artist", "limit": limit},
        timeout=10,
    )
    res.raise_for_status()
    data = res.json()["artists"]["items"]
    return [
        {
            "name": a["name"],
            "id": a["id"],
            "url": a["external_urls"]["spotify"]
        }
        for a in data
    ]


@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    """Get an artist’s top tracks."""
    token = get_spotify_token()
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"market": market},
        timeout=10,
    )
    res.raise_for_status()
    data = res.json()["tracks"]
    return {
        "artist_id": artist_id,
        "tracks": [
            {"name": t["name"], "url": t["external_urls"]["spotify"]}
            for t in data
        ]
    }


@mcp.tool()
def get_artist_albums(artist_id: str, limit: int = 10):
    """Fetch albums and singles for an artist."""
    token = get_spotify_token()
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers={"Authorization": f"Bearer {token}"},
        params={"include_groups": "album,single", "limit": limit},
        timeout=10,
    )
    res.raise_for_status()
    albums = res.json()["items"]
    return [
        {
            "name": a["name"],
            "release_date": a["release_date"],
            "id": a["id"],
            "url": a["external_urls"]["spotify"]
        }
        for a in albums
    ]

# ───────────────────────────
# 🌐 Discovery + Health Routes
# ───────────────────────────
@app.get("/")
async def root():
    return JSONResponse({
        "server": "Spotify MCP Server 🎧",
        "status": "running",
        "message": "Welcome to Ivy’s Spotify MCP endpoint!"
    })

@app.get("/mcp/manifest")
async def manifest():
    """Return MCP's registered tools for Copilot Studio discovery."""
    return JSONResponse(mcp.describe())

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    """Expose MCP metadata for Copilot Studio."""
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Spotify MCP Server 🎧",
        "name_for_model": "spotify-mcp",
        "description_for_model": (
            "Connects to Spotify Web API via MCP. "
            "Provides tools like search_artist_by_name, get_artist_top_tracks, and get_artist_albums."
        ),
        "auth": {"type": "none"},
        "api": {
            "type": "mcp",
            "protocol": "mcp-streamable-1.0",
            "url": "https://spotify-mcp-hha8cccmgnete3fm.australiaeast-01.azurewebsites.net/mcp"
        },
        "logo_url": "https://developer.spotify.com/assets/branding-guidelines/icon1.svg",
        "contact_email": "ivy.fiecas@example.com",
        "legal_info_url": "https://developer.spotify.com/terms/"
    })

# ───────────────────────────
# 🏁 Entry Point
# ───────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    workers = max(1, (multiprocessing.cpu_count() * 2) + 1)
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=workers)
