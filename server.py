"""
Spotify MCP Server 🎧
=====================
Author: Ivy Fiecas-Borjal
Description:
    A Model Context Protocol (MCP) server that connects to the Spotify Web API.

Features:
    🎵 Search artists by name
    🔝 Get top tracks
    💿 Fetch albums and tracks
    🎚️ Get audio features
    🎼 Summarize artist audio profiles
    🎤 Fetch solo songs only (filters collaborations)
"""

import os
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# 🔧 Environment Setup
# ─────────────────────────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("⚠️ Warning: Missing Spotify credentials — API tools will fail without them.")

# ─────────────────────────────────────────────
# ⚙️ Initialize Flask + MCP
# ─────────────────────────────────────────────
app = Flask(__name__)
mcp = FastMCP("spotify-mcp")

# ─────────────────────────────────────────────
# 🔐 Helper: Get Spotify Access Token
# ─────────────────────────────────────────────
def get_spotify_token() -> str:
    """Get Spotify access token via Client Credentials flow."""
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    res.raise_for_status()
    return res.json()["access_token"]

# ─────────────────────────────────────────────
# 🔍 Tool 1: Search Artist by Name
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

# ─────────────────────────────────────────────
# 🎵 Tool 2: Get Artist Top Tracks
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    """Return an artist’s top tracks by popularity."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market},
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

# ─────────────────────────────────────────────
# 💿 Tool 3: Get Artist Albums (with optional tracks)
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_albums(artist_id: str, include_tracks: bool = True):
    """Fetch albums and singles for a given artist."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 50, "market": "US"},
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
            tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers)
            tr.raise_for_status()
            album["tracks"] = [
                {"id": t["id"], "name": t["name"], "track_number": t["track_number"]}
                for t in tr.json().get("items", [])
            ]
        albums.append(album)
    return {"artist_id": artist_id, "albums": albums}

# ─────────────────────────────────────────────
# 🎚️ Tool 4: Get Audio Features by Track IDs
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# 🎼 Tool 5: Get Artist Audio Profile Summary
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_audio_profile(artist_id: str):
    """Fetch and summarize all audio features for an artist’s tracks."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}

    artist = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    artist.raise_for_status()
    artist_name = artist.json().get("name", "Unknown Artist")

    albums = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 50, "market": "US"},
    )
    albums.raise_for_status()
    albums = albums.json().get("items", [])

    track_ids = []
    for a in albums:
        tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers)
        tr.raise_for_status()
        for t in tr.json().get("items", []):
            track_ids.append(t["id"])
    if not track_ids:
        return {"message": "No tracks found for this artist."}

    all_features = []
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i + 100]
        feats = requests.get(
            "https://api.spotify.com/v1/audio-features",
            headers=headers,
            params={"ids": ",".join(batch)},
        )
        feats.raise_for_status()
        all_features.extend([f for f in feats.json().get("audio_features", []) if f])

    def avg(field):
        vals = [f[field] for f in all_features if f.get(field)]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    summary = {
        "avg_danceability": avg("danceability"),
        "avg_energy": avg("energy"),
        "avg_valence": avg("valence"),
        "avg_instrumentalness": avg("instrumentalness"),
        "avg_speechiness": avg("speechiness"),
        "avg_tempo": avg("tempo"),
        "total_tracks": len(all_features),
    }

    return {"artist_name": artist_name, "artist_id": artist_id, "summary": summary}

# ─────────────────────────────────────────────
# 🎤 Tool 6: Get Artist’s Solo Songs
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_own_tracks(artist_id: str):
    """Fetch only tracks where the artist is the *primary* performer."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}

    artist_info = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    artist_info.raise_for_status()
    artist_name = artist_info.json().get("name", "Unknown Artist")

    albums = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers=headers,
        params={"include_groups": "album,single", "limit": 50, "market": "US"},
    )
    albums.raise_for_status()
    albums = albums.json().get("items", [])

    songs = []
    for a in albums:
        tr = requests.get(f"https://api.spotify.com/v1/albums/{a['id']}/tracks", headers=headers)
        tr.raise_for_status()
        for t in tr.json().get("items", []):
            if t["artists"] and t["artists"][0]["name"].lower() == artist_name.lower():
                songs.append({
                    "id": t["id"],
                    "name": t["name"],
                    "album": a["name"],
                    "release_date": a["release_date"],
                    "url": t["external_urls"]["spotify"]
                })

    return {
        "artist_name": artist_name,
        "artist_id": artist_id,
        "total_songs": len(songs),
        "songs": songs[:25]
    }

# ─────────────────────────────────────────────
# 🌐 Minimal Flask Route (for Azure health check)
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "status": "ok",
        "message": "Spotify MCP Server is running 🎵",
        "tools": len(mcp.tools),
    })

# ─────────────────────────────────────────────
# 🏁 Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Local MCP dev mode
    if os.getenv("RUN_MCP_DEV"):
        print("🎧 Spotify MCP Server running — open MCP Inspector at http://localhost:6274")
        mcp.run()
    else:
        # Azure entry point
        port = int(os.environ.get("PORT", 8000))
        print(f"🚀 Starting Flask app on port {port}")
        app.run(host="0.0.0.0", port=port)
