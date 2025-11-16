from typing import Any
import os
import logging
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

# Core functions
def search_artist_by_name(artist_name: str) -> Any:
    """Search Spotify for an artist by name."""
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

def get_artist_top_tracks(artist_id: str) -> Any:
    """Get an artist's top tracks in AU market."""
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

def get_artist_albums(artist_id: str) -> Any:
    """Get an artist's albums."""
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

# Create FastAPI app
app = FastAPI(title="Spotify MCP REST API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class SearchArtistRequest(BaseModel):
    artist_name: str

class ArtistIdRequest(BaseModel):
    artist_id: str

# REST endpoints
@app.post("/search-artist")
async def search_artist_endpoint(request: SearchArtistRequest):
    """REST endpoint for searching artists"""
    logger.info(f"Search request for artist: {request.artist_name}")
    result = search_artist_by_name(request.artist_name)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/artist-top-tracks")
async def top_tracks_endpoint(request: ArtistIdRequest):
    """REST endpoint for getting top tracks"""
    logger.info(f"Top tracks request for artist: {request.artist_id}")
    result = get_artist_top_tracks(request.artist_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/artist-albums")
async def albums_endpoint(request: ArtistIdRequest):
    """REST endpoint for getting albums"""
    logger.info(f"Albums request for artist: {request.artist_id}")
    result = get_artist_albums(request.artist_id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Spotify MCP Server",
        "endpoints": ["/search-artist", "/artist-top-tracks", "/artist-albums"]
    }

@app.get("/health")
async def health():
    """Health check for Azure"""
    return {"status": "ok"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on 0.0.0.0:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
