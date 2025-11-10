import azure.functions as func
import json
import traceback

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        import os
        import requests
        from dotenv import load_dotenv
        load_dotenv()

        cid = os.getenv("SPOTIFY_CLIENT_ID")
        csecret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not cid or not csecret:
            raise Exception("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in environment settings")

        # Just test Spotify API connectivity
        res = requests.get("https://api.spotify.com", timeout=5)
        status = res.status_code

        return func.HttpResponse(
            json.dumps({"message": "Spotify MCP reachable", "status": status}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        trace = traceback.format_exc()
        return func.HttpResponse(
            json.dumps({"error": str(e), "trace": trace}),
            mimetype="application/json",
            status_code=500
        )
