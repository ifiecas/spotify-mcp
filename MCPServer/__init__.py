import azure.functions as func
import os
import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables (Spotify credentials)
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

mcp = FastMCP("spotify-mcp")

# 🔐 Get access token
def get_spotify_token():
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    res.raise_for_status()
    return res.json()["access_token"]

# 🎵 Tool 1: Search Artist by Name
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": artist_name, "type": "artist", "limit": limit},
    )
    data = res.json().get("artists", {}).get("items", [])
    return [
        {"name": a["name"], "id": a["id"], "followers": a["followers"]["total"], "genres": a.get("genres", [])}
        for a in data
    ]

# 🔝 Tool 2: Get Artist Top Tracks
@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market},
    )
    return res.json().get("tracks", [])

# Azure Function entry
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        tool = body.get("tool")
        args = body.get("args", {})

        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        else:
            result = {"message": "Unknown tool requested."}

        return func.HttpResponse(
            body=str(result),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)
