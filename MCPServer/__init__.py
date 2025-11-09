import azure.functions as func
import os
import json
import logging
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# 🔧 Environment Setup
# ─────────────────────────────────────────────
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

mcp = FastMCP("spotify-mcp")

# ─────────────────────────────────────────────
# 🔐 Helper: Get Spotify Access Token
# ─────────────────────────────────────────────
def get_spotify_token():
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    res.raise_for_status()
    return res.json()["access_token"]

# ─────────────────────────────────────────────
# 🎵 Tool 1: Search Artist by Name
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
    data = res.json().get("artists", {}).get("items", [])
    return [
        {
            "name": a["name"],
            "id": a["id"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
        }
        for a in data
    ]

# ─────────────────────────────────────────────
# 🔝 Tool 2: Get Artist Top Tracks
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
# 🧩 Azure Function Entry Point
# ─────────────────────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        logging.info(f"🔹 Request received: {body}")

        tool = body.get("tool")
        args = body.get("args") or {k.split("args.")[1]: v for k, v in body.items() if k.startswith("args.")}

        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        else:
            result = {"error": "Unknown tool requested."}

        # ─────────────────────────────────────
        # 🧠 Handle SSE / MCP responses
        # ─────────────────────────────────────
        if isinstance(result, str) and "event:" in result and "data:" in result:
            for line in result.splitlines():
                if line.startswith("data:"):
                    payload = line.replace("data:", "").strip()
                    try:
                        data = json.loads(payload)
                        if isinstance(data.get("id"), int):
                            data["id"] = str(data["id"])
                        result = data
                        break
                    except json.JSONDecodeError:
                        logging.error("Failed to decode SSE data payload.")

        # Always return JSON
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"❌ Error processing request: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
