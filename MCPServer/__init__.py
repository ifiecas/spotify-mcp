from typing import Any
import logging
import requests
from fastmcp.server import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.errors import ToolError

# Import local config
from config import API_TOKEN        # OutScrapper token
from config import LOCAL_TOKEN      # Token from Copilot Studio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Middleware for Copilot Studio authentication
class UserAuthMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):

        headers = get_http_headers()
        mcp_api_key = headers.get("api-key")

        if not mcp_api_key:
            raise ToolError("Access denied: missing api key")

        if not mcp_api_key.startswith("Bearer "):
            raise ToolError("Access denied: invalid token format")

        token = mcp_api_key.replace("Bearer", "").strip()

        if token != LOCAL_TOKEN:
            raise ToolError("Access denied: invalid token")

        return await call_next(context)

# Initialize FastMCP server
# Note: host and port must match your deployment
mcp = FastMCP(
    "hotels-mcp",
    host="0.0.0.0",      # For Azure or local VM
    port=8000
)

mcp.add_middleware(UserAuthMiddleware())

# Resource example
@mcp.resource("file://app.log")
def get_log_file() -> str:
    """Returns log file content"""
    try:
        with open("app.log", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "No logs found"

# Book a hotel
@mcp.tool()
async def book_hotel(hotel_name: str) -> str:
    hotel_name = hotel_name.strip()
    return f"Hotel {hotel_name} has been booked successfully"

# Get reviews using OutScrapper
@mcp.tool()
async def get_hotel_reviews(hotel_name: str) -> Any:
    hotel_name = hotel_name.replace("\n", "").replace("\r", "")

    url = (
        "https://api.app.outscraper.com/maps/reviews-v3"
        f"?query={hotel_name}&async=false&reviewsLimit=10"
    )

    headers = {
        "x-api-key": API_TOKEN,
        "Content-Type": "application/json"
    }

    logger.info(f"Calling: {url}")

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info(str(response.json()))
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling API: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
