import azure.functions as func
import logging
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("✅ MCPServer ping function invoked")
    return func.HttpResponse(
        json.dumps({"message": "🎧 Spotify MCP server base function is alive!"}),
        status_code=200,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )
