import os, requests, logging, multiprocessing, uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from middleware import AuthMiddleware   # same structure as the Microsoft sample

load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# ─── MCP setup ─────────────────────────────────────────────
mcp = FastMCP("🎧 Spotify MCP Server", stateless_http=True)
app = mcp.streamable_http_app()        # Starlette app
app.add_middleware(AuthMiddleware)     # optional API-key auth
app.debug = False
logging.basicConfig(level=logging.INFO)

# ─── Spotify helper ────────────────────────────────────────
def get_spotify_token():
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]

# ─── MCP Tools ─────────────────────────────────────────────
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5):
    """Search for artists by name and return their Spotify IDs."""
    token = get_spotify_token()
    r = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": artist_name, "type": "artist", "limit": limit},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()["artists"]["items"]
    return [{"name": a["name"], "id": a["id"], "url": a["external_urls"]["spotify"]} for a in data]

@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    """Return an artist’s top tracks."""
    token = get_spotify_token()
    r = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"market": market},
        timeout=10,
    )
    r.raise_for_status()
    tracks = r.json()["tracks"]
    return {"artist_id": artist_id, "tracks": [{"name": t["name"], "url": t["external_urls"]["spotify"]} for t in tracks]}

# Add other tools (albums, audio features, etc.) the same way…

# ─── Root Route ────────────────────────────────────────────
@app.route("/")
async def root(request):
    from starlette.responses import PlainTextResponse
    return PlainTextResponse("🎧 Spotify MCP Server is running ✅")

# ─── Run server (Azure or local) ───────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    workers = (multiprocessing.cpu_count() * 2) + 1
    logging.info(f"🚀 Spotify MCP running on http://0.0.0.0:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, workers=workers)
