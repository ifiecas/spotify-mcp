from typing import Any, Optional
import os
import logging
import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request

# Load environment variables
load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")  # must be supplied by Azure

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise EnvironmentError("Missing Spotify credentials (CLIENT ID + SECRET)")

if not LOCAL_TOKEN:
    raise EnvironmentError("Missing LOCAL_TOKEN env variable")

PORT = int(os.getenv("PORT", "8000"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp")

# Create MCP server
mcp = FastMCP("spotify-mcp")


# ------------------------------------------------------
# AUTHENTICATION MIDDLEWARE
# ------------------------------------------------------
class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Validates Bearer token for MCP endpoints"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for root path
        if request.url.path == "/":
            return await call_next(request)
        
        # Check for MCP endpoints
        if "/mcp" in request.url.path:
            raw = None
            
            # Check Authorization header (case-insensitive)
            auth_header = request.headers.get("authorization") or request.headers.get("api-key")
            
            if not auth_header:
                logger.warning(f"No authorization header found")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "message": "Missing authorization header"}
                )
            
            if not auth_header.startswith("Bearer "):
                logger.warning(f"Invalid auth format")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "message": "Invalid authorization format. Use: Bearer <token>"}
                )
            
            token = auth_header.replace("Bearer ", "").strip()
            if token != LOCAL_TOKEN:
                logger.warning("Token validation failed")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "message": "Invalid token"}
                )
            
            logger.info("✅ Token validation successful")
        
        response = await call_next(request)
        return response


# ------------------------------------------------------
# SPOTIFY CLIENT CREDENTIALS TOKEN
# ------------------------------------------------------
def get_spotify_token() -> Optional[str]:
    """Get Spotify API access token using client credentials flow"""
    try:
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        logger.error(f"Spotify authentication failed: {e}")
        return None


# ------------------------------------------------------
# TOOL: Search Artist
# ------------------------------------------------------
@mcp.tool()
def search_artist_by_name(artist_name: str) -> Any:
    """Search for artists on Spotify by name
    
    Args:
        artist_name: The name of the artist to search for
    
    Returns:
        Spotify search results with artist information
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            params={"q": artist_name, "type": "artist", "limit": 5},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": str(e)}


# ------------------------------------------------------
# TOOL: Get Top Tracks
# ------------------------------------------------------
@mcp.tool()
def get_artist_top_tracks(artist_id: str) -> Any:
    """Get top tracks for a Spotify artist
    
    Args:
        artist_id: The Spotify ID of the artist
    
    Returns:
        List of top tracks with audio features
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
            params={"market": "AU"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get top tracks failed: {e}")
        return {"error": str(e)}


# ------------------------------------------------------
# TOOL: Get Albums
# ------------------------------------------------------
@mcp.tool()
def get_artist_albums(artist_id: str) -> Any:
    """Get albums for a Spotify artist
    
    Args:
        artist_id: The Spotify ID of the artist
    
    Returns:
        List of albums for the artist
    """
    token = get_spotify_token()
    if not token:
        return {"error": "Spotify authentication failed"}

    try:
        resp = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/albums",
            params={"market": "AU", "limit": 10},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Get albums failed: {e}")
        return {"error": str(e)}


# ------------------------------------------------------
# RUN SERVER
# ------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"🎵 Spotify MCP Server starting...")
    logger.info(f"   Port: {PORT}")
    logger.info(f"   Endpoint: /mcp")
    logger.info(f"   Authentication: Bearer token required")
    
    # Get the HTTP app
    app = mcp.http_app()
    
    # Add middleware manually
    app.add_middleware(BearerTokenMiddleware)
    
    # Run with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
