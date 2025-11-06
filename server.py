# server.py
import os
import requests
import logging
import multiprocessing
import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.responses import PlainTextResponse

# ───────────────────────────
# 🔧 Setup
# ───────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

mcp = FastMCP("🎧 Spotify MCP Server", stateless_http=True)
app = mcp.streamable_http_app()
app.debug = False
logging.basicConfig(level=logging.INFO)

# ───────────────────────────
# 🔐 Helper: Spotify Token
# ───────────────────────────
def get_spotify_token():
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
    return [{"name": a["name"], "id": a["id"], "url": a["external_urls"]["spotify"]} for a in data]


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
    return {"artist_id": artist_id, "tracks": [{"name": t["name"], "url": t["external_urls"]["spotify"]} for t in data]}


@mcp.tool()
def get_artist_albums(artist_id: str):
    """Fetch albums and singles for an artist."""
    token = get_spotify_token()
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers={"Authorization": f"Bearer {token}"},
        params={"include_groups": "album,single", "limit": 20},
        timeout=10,
    )
    res.raise_for_status()
    albums = res.json()["items"]
    return [{"name": a["name"], "release_date": a["release_date"], "id": a["id"]} for a in albums]


# ───────────────────────────
# 🌐 Root Route (for Azure)
# ───────────────────────────
@app.route("/")
async def root(request):
    return PlainTextResponse("🎧 Spotify MCP Server is running ✅")

# ───────────────────────────
# 🏁 Run on Azure or Local
# ───────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    workers = (multiprocessing.cpu_count() * 2) + 1
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=workers)
