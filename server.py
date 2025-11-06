"""
Spotify MCP Server 🎧
=====================
Author: Ivy Fiecas-Borjal

Description:
    A Model Context Protocol (MCP) server that connects to the Spotify Web API
    and exposes tools usable by Microsoft Copilot Studio, Logic Apps, or Azure AI.

Tools Exposed:
    🎵 search_artist_by_name     → Find artists by name
    🔝 get_artist_top_tracks     → Retrieve top tracks
    💿 get_artist_albums         → List albums & tracks
    🎚️ get_audio_features        → Fetch track audio features
    🎼 get_artist_audio_profile  → Summarize artist audio profile
    🎤 get_artist_own_tracks     → Filter solo songs only

Setup:
    1. Create a `.env` file with:
         SPOTIFY_CLIENT_ID=your_client_id
         SPOTIFY_CLIENT_SECRET=your_client_secret
    2. Install dependencies:
         pip install requests python-dotenv mcp flask gunicorn
    3. Local test:
         python server.py
    4. Azure startup command:
         gunicorn --bind=0.0.0.0:$PORT server:app
    5. Deployed endpoint:
         https://spotify-mcp-hha8cccmgnete3fm.australiaeast-01.azurewebsites.net
"""

import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# 🔧 Environment Setup
# ─────────────────────────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("❌ Missing Spotify credentials. Add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")

# ─────────────────────────────────────────────
# ⚙️ Initialize MCP Server
# ─────────────────────────────────────────────
mcp = FastMCP("spotify-mcp")

# ─────────────────────────────────────────────
# 🔐 Helper: Get Spotify Access Token
# ─────────────────────────────────────────────
def get_spotify_token() -> str:
    try:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        res.raise_for_status()
        return res.json()["access_token"]
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve Spotify token: {e}")

# ─────────────────────────────────────────────
# 🎵 MCP Tools
# ─────────────────────────────────────────────
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5):
    """Search for artists by name and return their Spotify IDs."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": artist_name, "type": "artist", "limit": limit},
        timeout=10,
    )
    res.raise_for_status()
    data = res.json().get("artists", {}).get("items", [])
    if not data:
        return {"message": f"No artists found for '{artist_name}'."}
    return [
        {
            "name": a["name"],
            "id": a["id"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
            "url": a["external_urls"]["spotify"],
        }
        for a in data
    ]


@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    """Return an artist’s top tracks by popularity."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market},
        timeout=10,
    )
    res.raise_for_status()
    data = res.json().get("tracks", [])
    return {
        "artist_id": artist_id,
        "total_tracks": len(data),
        "tracks": [
            {
                "id": t["id"],
                "name": t["name"],
                "album": t["album"]["name"],
                "release_date": t["album"]["release_date"],
                "popularity": t["popularity"],
                "url": t["external_urls"]["spotify"],
            }
            for t in data
        ],
    }


@mcp.tool()
def get_artist_albums(artist_id: str, include_tracks: bool = True):
    """Fetch albums and singles for a given artist."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 50, "market": "US"},
        timeout=10,
    )
    res.raise_for_status()
    albums_data = res.json().get("items", [])
    albums = []
    for a in albums_data:
        album = {
            "album_id": a["id"],
            "album_name": a["name"],
            "release_date": a["release_date"],
            "total_tracks": a["total_tracks"],
            "url": a["external_urls"]["spotify"],
        }
        if include_tracks:
            tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers, timeout=10)
            tr.raise_for_status()
            album["tracks"] = [
                {"id": t["id"], "name": t["name"], "track_number": t["track_number"]}
                for t in tr.json().get("items", [])
            ]
        albums.append(album)
    return {"artist_id": artist_id, "albums": albums}


@mcp.tool()
def get_audio_features(track_ids: list):
    """Fetch Spotify audio features for up to 100 tracks."""
    if not track_ids:
        raise ValueError("No track IDs provided.")
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
    return {
        "count": len(data),
        "features": [
            {
                "id": f["id"],
                "danceability": f["danceability"],
                "energy": f["energy"],
                "valence": f["valence"],
                "instrumentalness": f["instrumentalness"],
                "speechiness": f["speechiness"],
                "tempo": f["tempo"],
            }
            for f in data if f
        ],
    }


@mcp.tool()
def get_artist_audio_profile(artist_id: str):
    """Fetch and summarize all audio features for an artist’s tracks."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    artist_info = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers, timeout=10)
    artist_info.raise_for_status()
    artist_name = artist_info.json().get("name", "Unknown Artist")

    albums = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 50, "market": "US"},
        timeout=10,
    )
    albums.raise_for_status()
    albums = albums.json().get("items", [])
    track_ids = []
    for a in albums:
        tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers, timeout=10)
        tr.raise_for_status()
        for t in tr.json().get("items", []):
            track_ids.append(t["id"])
    if not track_ids:
        return {"message": f"No tracks found for {artist_name}."}

    features = []
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i + 100]
        feats = requests.get(
            "https://api.spotify.com/v1/audio-features",
            headers=headers,
            params={"ids": ",".join(batch)},
            timeout=10,
        )
        feats.raise_for_status()
        features.extend([f for f in feats.json().get("audio_features", []) if f])

    if not features:
        return {"message": f"No audio features found for {artist_name}."}

    def avg(field): return round(sum(f[field] for f in features if f.get(field)) / len(features), 3)
    summary = {k: avg(k) for k in ["danceability", "energy", "valence", "instrumentalness", "speechiness", "tempo"]}
    summary["total_tracks"] = len(features)
    return {"artist_name": artist_name, "artist_id": artist_id, "summary": summary, "sample_features": features[:5]}


@mcp.tool()
def get_artist_own_tracks(artist_id: str):
    """Fetch only tracks where the artist is the *primary* performer."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    artist_info = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers, timeout=10)
    artist_info.raise_for_status()
    artist_name = artist_info.json().get("name", "Unknown Artist")

    albums = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 50, "market": "US"},
        timeout=10,
    )
    albums.raise_for_status()
    albums = albums.json().get("items", [])
    songs = []
    for a in albums:
        tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers, timeout=10)
        tr.raise_for_status()
        for t in tr.json().get("items", []):
            if t["artists"] and t["artists"][0]["name"].lower() == artist_name.lower():
                songs.append({
                    "id": t["id"],
                    "name": t["name"],
                    "album": a["name"],
                    "release_date": a["release_date"],
                    "url": t["external_urls"]["spotify"],
                })
    if not songs:
        return {"message": f"No solo songs found for {artist_name}."}
    return {"artist_name": artist_name, "artist_id": artist_id, "total_songs": len(songs), "songs": songs[:25]}

# ─────────────────────────────────────────────
# 🌐 Flask App for Azure Hosting + MCP Discovery
# ─────────────────────────────────────────────
app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "server": "Spotify MCP Server 🎧",
        "status": "running",
        "message": "Welcome to Ivy’s Spotify MCP endpoint!"
    })

@app.route("/.well-known/ai-plugin.json", methods=["GET"])
def plugin_manifest():
    """Expose MCP metadata for Copilot Studio discovery."""
    return jsonify({
        "schema_version": "v1",
        "name_for_human": "Spotify MCP Server 🎧",
        "name_for_model": "spotify-mcp",
        "description_for_model": (
            "Connects to Spotify Web API via MCP. "
            "Provides tools: search_artist_by_name, get_artist_top_tracks, "
            "get_artist_albums, get_audio_features, get_artist_audio_profile, get_artist_own_tracks."
        ),
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": "https://spotify-mcp-hha8cccmgnete3fm.australiaeast-01.azurewebsites.net/mcp"
        },
        "logo_url": "https://developer.spotify.com/assets/branding-guidelines/icon1.svg",
        "contact_email": "ivy.fiecas@example.com",
        "legal_info_url": "https://developer.spotify.com/terms/"
    })

@app.route("/mcp/manifest", methods=["GET"])
def mcp_manifest():
    """Return MCP's registered tools for debugging."""
    return jsonify(mcp.describe())

@app.route("/mcp", methods=["POST"])
def invoke_mcp():
    """Main MCP entrypoint for Copilot Studio / Power Apps."""
    try:
        return mcp.handle_http(request)
    except Exception as e:
        print("❌ MCP Error:", e)
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────
# 🏁 Entry Point (local debug)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🎧 Spotify MCP Server running on port {port}")
    app.run(host="0.0.0.0", port=port)
