import azure.functions as func
import logging
import os
import json
import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info("✅ Function triggered")
        cid = os.getenv("SPOTIFY_CLIENT_ID")
        secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not cid or not secret:
            raise RuntimeError("Missing Spotify credentials in Azure Configuration")

        # simple Spotify ping
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(cid, secret),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Spotify token failed: {r.status_code} → {r.text[:200]}")

        return func.HttpResponse(
            json.dumps({"message": "✅ Spotify MCP base function works", "status": r.status_code}),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.error(f"❌ {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )
