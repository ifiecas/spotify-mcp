import azure.functions as func
import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_spotify_token():
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    )
    res.raise_for_status()
    return res.json()["access_token"]

def search_artist_by_name(artist_name: str, limit=5):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": artist_name, "type": "artist", "limit": limit}
    )
    return res.json()

def get_artist_top_tracks(artist_id: str, market="US"):
    token = get_spotify_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers=headers,
        params={"market": market}
    )
    return res.json()

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # parse JSON safely
        try:
            body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                mimetype="application/json"
            )

        tool = body.get("tool")
        args = body.get("args", {})

        logging.info(f"🔹 Request received: tool={tool}, args={args}")

        if tool == "search_artist_by_name":
            result = search_artist_by_name(
                artist_name=args.get("artist_name", "Adele"),
                limit=int(args.get("limit", 5))
            )
        elif tool == "get_artist_top_tracks":
            result = get_artist_top_tracks(
                artist_id=args.get("artist_id"),
                market=args.get("market", "US")
            )
        else:
            result = {"message": "🎧 Spotify MCP debug — endpoint is alive!"}

        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        # return detailed debug error
        err = {"error": str(e), "type": str(type(e).__name__)}
        logging.error(f"❌ Exception: {err}", exc_info=True)
        return func.HttpResponse(json.dumps(err), status_code=500, mimetype="application/json")
