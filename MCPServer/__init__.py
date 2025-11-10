import azure.functions as func
import json
import logging
import os
import requests
from dotenv import load_dotenv

# ─────────────────────────────
# 🎧 Main Azure Function
# ─────────────────────────────
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🎧 Spotify MCP Function triggered")

    try:
        load_dotenv()

        # Retrieve Spotify credentials from environment
        SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
        SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            return func.HttpResponse(
                json.dumps({"error": "Missing Spotify credentials"}),
                mimetype="application/json",
                status_code=400
            )

        # Get Spotify access token
        token_res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        )
        token_res.raise_for_status()
        token = token_res.json().get("access_token")

        # Check if artist name was passed
        try:
            body = req.get_json()
        except ValueError:
            body = {}

        artist_name = body.get("artist_name")

        if not artist_name:
            return func.HttpResponse(
                json.dumps({
                    "message": "🎧 Spotify MCP server is alive!",
                    "hint": "POST with {'artist_name': 'Adele'} to search tracks."
                }),
                mimetype="application/json",
                status_code=200
            )

        # Search artist by name
        search_res = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": artist_name, "type": "artist", "limit": 1},
        )
        search_res.raise_for_status()
        artists = search_res.json().get("artists", {}).get("items", [])

        if not artists:
            return func.HttpResponse(
                json.dumps({"message": f"No artists found for '{artist_name}'."}),
                mimetype="application/json",
                status_code=404
            )

        artist = artists[0]
        artist_id = artist["id"]

        # Get artist top tracks
        tracks_res = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
            headers={"Authorization": f"Bearer {token}"},
            params={"market": "US"},
        )
        tracks_res.raise_for_status()
        tracks = [
            {"name": t["name"], "popularity": t["popularity"], "url": t["external_urls"]["spotify"]}
            for t in tracks_res.json().get("tracks", [])
        ]

        result = {
            "artist": artist["name"],
            "followers": artist["followers"]["total"],
            "genres": artist.get("genres", []),
            "popularity": artist["popularity"],
            "top_tracks": tracks[:5]
        }

        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
