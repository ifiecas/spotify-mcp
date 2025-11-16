from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN", "ivymcp")

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials in environment")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure will set PORT, default to 8000 for local
PORT = int(os.getenv("PORT", "8000"))

# FastMCP server
mcp = FastMCP("spotify-mcp")

# Helper: get Spotify auth token
def get_spotify_token() -> str | None:
    url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    try:
        resp = requests.post(url, data=data, auth=auth, timeout=10)
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            logger.error("No access_token in Spotify response")
        return token
    except Exception as e:
        logger.error(f"Spotify token error: {e}")
        return None

# MCP Tool 1 - search artist
@mcp.tool()
def search_artist_by_name(artist_name: str) -> Any:
    """
    Search Spotify for an artist by name.
    
    Args:
        artist_name: The name of the artist to search for
        
    Returns:
        JSON object containing search results with artist information
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Could not authenticate with Spotify"}
    
    url = "https://api.spotify.com/v1/search"
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 5,
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify search error: {e}")
        return {"error": str(e)}

# MCP Tool 2 - top tracks
@mcp.tool()
def get_artist_top_tracks(artist_id: str) -> Any:
    """
    Get an artist's top tracks in AU market.
    
    Args:
        artist_id: The Spotify artist ID
        
    Returns:
        JSON object containing the artist's top tracks
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}
    
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    params = {"market": "AU"}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify top tracks error: {e}")
        return {"error": str(e)}

# MCP Tool 3 - artist albums
@mcp.tool()
def get_artist_albums(artist_id: str) -> Any:
    """
    Get an artist's albums.
    
    Args:
        artist_id: The Spotify artist ID
        
    Returns:
        JSON object containing the artist's albums
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}
    
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    params = {
        "market": "AU",
        "limit": 10,
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Spotify albums error: {e}")
        return {"error": str(e)}

# Run FastMCP with streamable-http transport
if __name__ == "__main__":
    from starlette.middleware.cors import CORSMiddleware
    from fastapi import Request, Response
    
    # Get the ASGI app from FastMCP
    app = mcp.get_asgi_app()
    
    # Add CORS middleware for Power Platform
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "*",
            "https://make.powerapps.com",
            "https://make.powerautomate.com", 
            "https://*.microsoft.com",
            "https://copilotstudio.microsoft.com"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Add authentication middleware
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """Validate Bearer token"""
        # Skip auth for health check
        if request.url.path == "/":
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response(
                content='{"error": "Missing or invalid Authorization header"}',
                status_code=401,
                media_type="application/json"
            )
        
        token = auth_header.replace("Bearer ", "")
        if token != LOCAL_TOKEN:
            return Response(
                content='{"error": "Invalid authentication token"}',
                status_code=401,
                media_type="application/json"
            )
        
        return await call_next(request)
    
    # Add root health check
    @app.get("/")
    async def health():
        return {
            "status": "healthy",
            "service": "Spotify MCP Server",
            "transport": "streamable-http",
            "tools": ["search_artist_by_name", "get_artist_top_tracks", "get_artist_albums"]
        }
    
    import uvicorn
    logger.info(f"Starting Spotify MCP Server on 0.0.0.0:{PORT}")
    logger.info("MCP endpoint available at /mcp")
    logger.info("Tools: search_artist_by_name, get_artist_top_tracks, get_artist_albums")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
