import azure.functions as func
import json
import logging
import os
import requests
from dotenv import load_dotenv

# ─────────────────────────────
#  Load environment
# ─────────────────────────────
load_dotenv()

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🎧 Spotify MCP Function triggered.")
    try:
        # Simple heartbeat endpoint
        if req.method == "GET":
            return func.HttpResponse(
                json.dumps({"message": "🎧 Spotify MCP test — endpoint is alive!"}),
                mimetype="application/json",
                status_code=200
            )

        # Parse body if POST
        body = req.get_json()
        logging.info(f"Incoming body: {body}")

        return func.HttpResponse(
            json.dumps({"echo": body}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"❌ Function error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
