import azure.functions as func
import logging
import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

mcp = FastMCP("spotify-mcp")

def get_spotify_token():
    res = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    res.raise_for_status()
    return res.json()["access_token"]

@mcp.tool()
def ping():
    return {"message": "Spotify MCP server is running on Azure!"}

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logging.info("⚡ MCP Function triggered.")
    return func.HttpResponse(
        '{"message": "Spotify MCP server is alive!"}',
        status_code=200,
        mimetype="application/json"
    )
