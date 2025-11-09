import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        '{"message": "Spotify MCP server is alive!"}',
        status_code=200,
        mimetype="application/json"
    )
