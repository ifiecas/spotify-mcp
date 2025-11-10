import azure.functions as func
import os
import json
import logging
import time
import requests
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# 🔧 Load environment variables
# ─────────────────────────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    logging.warning("⚠️ Missing Spotify credentials in environment variables.")

# ─────────────────────────────────────────────
# 🔐 Access token cache
# ─────────────────────────────────────────────
_cached_token = None
_token_expiry = 0


def get_spotify_token():
    """Fetch a Spotify API token and cache it until expiry."""
    global _cached_token, _token_expiry
    now = time.time()

    # Return cached token if still valid
    if _cached_token and now < _token_expiry:
        return _cached_token

    url = "https://accounts.spotify.com/api/token"
    try:
        res = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        _cached_token = data["access_token"]
        _token_expiry = now + data.get("expires_in", 3600) - 30
        return _cached_token
    except Exception as e:
        logging.error(f"Failed to fetch Spotify token: {e}", exc_info=True)
        raise


# ─────────────────────────────────────────────
# 🎵 Tool 1: Search Artist by Name
# ─────────────────────────────────────────────
def search_artist_by_name(artist_name: str, limit: int = 5):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": artist_name, "type": "artist", "limit": limit}
    url = "https://api.spotify.com/v1/search"

    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()

    data = res.json().get("artists", {}).get("items", [])
    return [
        {
            "id": a["id"],
            "name": a["name"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
        }
        for a in data
    ]


# ─────────────────────────────────────────────
# 🔝 Tool 2: Get Artist Top Tracks
# ─────────────────────────────────────────────
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    res = requests.get(url, headers=headers, params={"market": market}, timeout=10)
    res.raise_for_status()
    return res.json().get("tracks", [])


# ─────────────────────────────────────────────
# 🧩 Azure Function Entry Point
# ─────────────────────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🎧 Spotify MCP Function triggered.")
    try:
        body = req.get_json()
    except ValueError:
        body = {}

    tool = body.get("tool")
    args = body.get("args", {})

    try:
        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        else:
            result = {"message": "Spotify MCP reachable", "status": 200}

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )

    except requests.exceptions.HTTPError as e:
        logging.error(f"Spotify API error: {e.response.text}")
        return func.HttpResponse(
            json.dumps({"error": "Spotify API error", "details": e.response.text}),
            mimetype="application/json",
            status_code=e.response.status_code,
        )
    except Exception as e:
        logging.error(f"Unhandled error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )
