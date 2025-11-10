import azure.functions as func
import json
import traceback
import os
import requests
from dotenv import load_dotenv

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Load env first
        load_dotenv()
        SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
        SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

        # Basic check before calling Spotify
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            raise ValueError("Missing Spotify credentials in environment variables.")

        # Test Spotify connection
        res = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        )
        res.raise_for_status()
        token = res.json().get("access_token")

        return func.HttpResponse(
            json.dumps({"message": "✅ Spotify MCP debug success!", "token_preview": token[:20]}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        # Return full traceback to see the problem
        tb = traceback.format_exc()
        error_json = {"error": str(e), "traceback": tb}
        return func.HttpResponse(
            json.dumps(error_json, indent=2),
            status_code=500,
            mimetype="application/json"
        )
