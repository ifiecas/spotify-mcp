import azure.functions as func
import os
import json
import logging
import requests

# ─────────────────────────────────────────────
# ⚙️ Setup
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    logging.warning("⚠️ Spotify credentials are missing from environment variables.")

# ─────────────────────────────────────────────
# 🔐 Spotify Token Helper
# ─────────────────────────────────────────────
def get_spotify_token():
    """Obtain Spotify API access token."""
    try:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        )
        res.raise_for_status()
        token = res.json()["access_token"]
        logging.info("✅ Spotify token retrieved successfully")
        return token
    except Exception as e:
        logging.error(f"❌ Spotify token error: {e}")
        raise RuntimeError("Failed to authenticate with Spotify API")

# ─────────────────────────────────────────────
# 🎵 Tool: Search Artist by Name
# ─────────────────────────────────────────────
def search_artist_by_name(artist_name: str, limit: int = 5):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": artist_name, "type": "artist", "limit": limit}
    res = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    res.raise_for_status()
    items = res.json().get("artists", {}).get("items", [])
    logging.info(f"🎤 Found {len(items)} artists for query '{artist_name}'")
    return [
        {
            "name": a["name"],
            "id": a["id"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
            "url": a["external_urls"]["spotify"],
        }
        for a in items
    ]

# ─────────────────────────────────────────────
# 🔝 Tool: Get Artist Top Tracks
# ─────────────────────────────────────────────
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    res = requests.get(url, headers=headers, params={"market": market})
    res.raise_for_status()
    tracks = res.json().get("tracks", [])
    logging.info(f"🎧 Retrieved {len(tracks)} top tracks for artist ID {artist_id}")
    return [
        {
            "name": t["name"],
            "album": t["album"]["name"],
            "release_date": t["album"]["release_date"],
            "popularity": t["popularity"],
            "url": t["external_urls"]["spotify"]
        }
        for t in tracks
    ]

# ─────────────────────────────────────────────
# 🧩 Azure Function HTTP Entry
# ─────────────────────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🚀 MCPServer Azure Function triggered")

    try:
        body = req.get_json(silent=True) or {}
        logging.info(f"📥 Request body: {body}")

        tool = body.get("tool")
        args = body.get("args", {})

        # Health check
        if not tool:
            return func.HttpResponse(
                json.dumps({"message": "🎧 Spotify MCP server is alive!"}),
                status_code=200,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Execute tool
        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        else:
            result = {"error": f"Unknown tool '{tool}'."}

        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except requests.exceptions.HTTPError as e:
        logging.error(f"Spotify API HTTP error: {e.response.text}")
        return func.HttpResponse(
            json.dumps({"error": "Spotify API error", "details": e.response.text}),
            status_code=e.response.status_code,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        logging.error(f"❌ Internal server error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "details": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
