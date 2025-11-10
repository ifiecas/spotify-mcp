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
# 🔐 Token Cache
# ─────────────────────────────────────────────
_cached_token = None
_token_expiry = 0


def get_spotify_token():
    """Fetch a Spotify API token and cache until expiry."""
    global _cached_token, _token_expiry
    now = time.time()

    if _cached_token and now < _token_expiry:
        return _cached_token

    try:
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
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market},
        timeout=10,
    )
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
def get_artist_albums(artist_id: str, include_tracks: bool = False):
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
def get_audio_features(track_ids: list):
    if not track_ids:
        return {"error": "No track IDs provided."}
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
def get_artist_profile(artist_id: str):
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
        return {"message": "No tracks found for artist."}

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
# 🧩 Tool 6: MCP Tool Discovery
# ─────────────────────────────────────────────
def get_available_tools():
    """Return full MCP schema for Copilot Studio discovery."""
    return {
        "tools": [
            {
                "name": "search_artist_by_name",
                "description": "Search Spotify artists by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "artist_name": {"type": "string"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["artist_name"],
                },
            },
            {
                "name": "get_artist_top_tracks",
                "description": "Retrieve top tracks for an artist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "artist_id": {"type": "string"},
                        "market": {"type": "string", "default": "US"},
                    },
                    "required": ["artist_id"],
                },
            },
            {
                "name": "get_artist_albums",
                "description": "Fetch artist albums or singles.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "artist_id": {"type": "string"},
                        "include_tracks": {"type": "boolean", "default": False},
                    },
                    "required": ["artist_id"],
                },
            },
            {
                "name": "get_audio_features",
                "description": "Retrieve detailed audio features for tracks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "track_ids": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["track_ids"],
                },
            },
            {
                "name": "get_artist_profile",
                "description": "Summarize average audio features for an artist.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "artist_id": {"type": "string"},
                    },
                    "required": ["artist_id"],
                },
            },
        ]
    }


# ─────────────────────────────────────────────
# 🩺 Health Check
# ─────────────────────────────────────────────
def health_check():
    return {"message": "🎧 Spotify MCP health OK", "status": 200}


# ─────────────────────────────────────────────
# 🧩 Azure Entry
# ─────────────────────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🎧 Spotify MCP Triggered")
    try:
        body = req.get_json()
    except ValueError:
        body = {}

    tool = body.get("tool", "")
    args = body.get("args", {})

    try:
        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        elif tool == "get_artist_albums":
            result = get_artist_albums(**args)
        elif tool == "get_audio_features":
            result = get_audio_features(**args)
        elif tool == "get_artist_profile":
            result = get_artist_profile(**args)
        elif tool == "get_available_tools":
            result = get_available_tools()
        elif tool == "health_check":
            result = health_check()
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
