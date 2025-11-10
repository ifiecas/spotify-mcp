import azure.functions as func
import os
import json
import logging

try:
    import requests
    logging.info("✅ requests module imported successfully")
except Exception as e:
    logging.error(f"❌ Failed to import requests: {e}")

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info("✅ MCPServer function started")

        cid = os.getenv("SPOTIFY_CLIENT_ID")
        secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not cid or not secret:
            raise ValueError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET")

        logging.info(f"🔹 SPOTIFY_CLIENT_ID found: {cid[:6]}...")

        # Spotify token test
        url = "https://accounts.spotify.com/api/token"
        data = {"grant_type": "client_credentials"}
        auth = (cid, secret)
        logging.info("🔸 Sending POST to Spotify token endpoint...")
        res = requests.post(url, data=data, auth=auth)

        logging.info(f"🔹 Spotify response: {res.status_code}")
        if res.status_code != 200:
            logging.error(f"❌ Spotify auth failed: {res.text}")
            return func.HttpResponse(
                json.dumps({"error": "Spotify auth failed", "details": res.text}),
                status_code=res.status_code,
                mimetype="application/json",
            )

        token = res.json().get("access_token", "none")
        logging.info("✅ Token retrieved successfully")

        return func.HttpResponse(
            json.dumps({"message": "Spotify MCP test passed", "token_preview": token[:10]}),
            status_code=200,
            mimetype="application/json",
        )

    except Exception as e:
        logging.error(f"❌ Exception occurred: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
