import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        '{"message": "🎧 Spotify MCP test — endpoint is alive!"}',
        mimetype="application/json"
    )
