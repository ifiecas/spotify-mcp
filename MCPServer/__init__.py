import azure.functions as func
import os
import json
import logging
import requests
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# 🔧 Setup and Environment
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    logging.warning("⚠️ Spotify credentials not found in App Settings.")

mcp = FastMCP("spotify-mcp")

# ─────────────────────────────────────────────
# 🔐 Helper: Spotify Token
# ─────────────────────────────────────────────
def get_spotify_token():
    """Get Spotify access token via Client Credentials flow."""
    try:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        )
        res.raise_for_status()
        return res.json()["access_token"]
    except Exception as e:
        logging.error(f"Spotify token request failed: {e}")
        raise RuntimeError("Spotify authentication error")

# ─────────────────────────────────────────────
# 🎵 Tool: Search Artist by Name
# ─────────────────────────────────────────────
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": artist_name, "type": "artist", "limit": limit},
    )
    res.raise_for_status()
    artists = res.json().get("artists", {}).get("items", [])
    return [
        {
            "name": a["name"],
            "id": a["id"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
            "url": a["external_urls"]["spotify"]
        }
        for a in artists
    ]

# ─────────────────────────────────────────────
# 🔝 Tool: Get Artist Top Tracks
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market},
    )
    res.raise_for_status()
    return res.json().get("tracks", [])

# ─────────────────────────────────────────────
# 🧩 Azure Function Entry
# ─────────────────────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse body safely
        body = req.get_json(silent=True) or {}
        logging.info(f"📥 Received body: {body}")

        tool = body.get("tool")
        args = body.get("args", {})

        # ── Health Check
        if not tool:
            return func.HttpResponse(
                json.dumps({"message": "🎧 Spotify MCP server is alive!"}),
                status_code=200,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # ── Dispatch tools
        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        else:
            result = {"error": f"Unknown tool: {tool}"}

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except requests.exceptions.HTTPError as e:
        logging.error(f"Spotify API error: {e}")
        return func.HttpResponse(
            json.dumps({"error": "Spotify API error", "details": e.response.text}),
            status_code=e.response.status_code,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"❌ Internal Error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
