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

# Early validation so missing credentials throw a clear error
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    logging.error("❌ Missing Spotify credentials in environment variables.")
    raise EnvironmentError("SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not set in Azure Function configuration.")

mcp = FastMCP("spotify-mcp")

# ─────────────────────────────────────────────
# 🔐 Helper: Get Spotify Access Token
# ─────────────────────────────────────────────
def get_spotify_token():
    """Authenticate with Spotify API using Client Credentials flow."""
    try:
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        )
        res.raise_for_status()
        token = res.json().get("access_token")
        if not token:
            raise ValueError("Spotify token missing in response.")
        return token
    except Exception as e:
        logging.error(f"❌ Failed to get Spotify access token: {e}", exc_info=True)
        raise

# ─────────────────────────────────────────────
# 🎵 Tool 1: Search Artist by Name
# ─────────────────────────────────────────────
@mcp.tool()
def search_artist_by_name(artist_name: str, limit: int = 5):
    """Search for artists by name."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": artist_name, "type": "artist", "limit": limit},
    )
    res.raise_for_status()
    artists = res.json().get("artists", {}).get("items", [])
    logging.info(f"🎤 Found {len(artists)} artists for '{artist_name}'.")
    return [
        {
            "name": a["name"],
            "id": a["id"],
            "followers": a["followers"]["total"],
            "genres": a.get("genres", []),
            "popularity": a["popularity"],
        }
        for a in artists
    ]

# ─────────────────────────────────────────────
# 🔝 Tool 2: Get Artist Top Tracks
# ─────────────────────────────────────────────
@mcp.tool()
def get_artist_top_tracks(artist_id: str, market: str = "US"):
    """Fetch the artist’s top tracks by Spotify ID."""
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market},
    )
    res.raise_for_status()
    tracks = res.json().get("tracks", [])
    logging.info(f"🎵 Retrieved {len(tracks)} top tracks for artist ID {artist_id}.")
    return tracks

# ─────────────────────────────────────────────
# 🧩 Azure Function Entry Point
# ─────────────────────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main Azure Function entry — acts as the MCP bridge endpoint."""
    try:
        body = req.get_json()
        logging.info(f"🔹 Incoming request body: {body}")

        tool = body.get("tool")
        args = body.get("args") or {k.split("args.")[1]: v for k, v in body.items() if k.startswith("args.")}

        if not tool:
            raise ValueError("Missing 'tool' in request body.")
        if not isinstance(args, dict):
            raise ValueError("'args' must be a dictionary.")

        # Select which MCP tool to invoke
        if tool == "search_artist_by_name":
            result = search_artist_by_name(**args)
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(**args)
        else:
            result = {"error": f"Unknown tool '{tool}' requested."}
            logging.warning(f"⚠️ Unknown tool called: {tool}")

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
                        logging.info("🧩 SSE payload unwrapped successfully.")
                        break
                    except json.JSONDecodeError:
                        logging.error("Failed to decode SSE JSON payload.", exc_info=True)

        # ─────────────────────────────────────
        # ✅ Return clean JSON response
        # ─────────────────────────────────────
        response_json = json.dumps(result, ensure_ascii=False)
        logging.info("✅ Function executed successfully.")
        return func.HttpResponse(
            response_json,
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"❌ Unhandled error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "hint": "Check Log Stream in Azure Portal for detailed traceback."
            }),
            status_code=500,
            mimetype="application/json"
        )
