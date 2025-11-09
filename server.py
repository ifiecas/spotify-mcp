import azure.functions as func
import os
import requests
from mcp.server.fastmcp import FastMCP

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

mcp = FastMCP("spotify-mcp")

@mcp.tool()
def ping():
    return {"message": "Spotify MCP server is running on Azure!"}

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        '{"message": "Spotify MCP server is alive!"}',
        status_code=200,
        mimetype="application/json"
    )
