import azure.functions as func
import json
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info("🎧 Spotify MCP basic endpoint triggered")
        return func.HttpResponse(
            json.dumps({"message": "🎧 Spotify MCP server base function is alive!"}),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error in MCP Function: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
