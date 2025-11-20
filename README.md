# 🎵 Spotify MCP Server

A **Model Context Protocol (MCP)** server that connects to the Spotify Web API, enabling AI agents in Microsoft Copilot Studio to search for artists, retrieve top tracks, and get album information.

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/)

---

## 🌟 Features

✅ **Search Artists** - Find artists on Spotify by name  
✅ **Search Tracks** - Search for songs by name, artist, or both  
✅ **Get Top Tracks** - Retrieve an artist's most popular tracks  
✅ **Get Albums** - List albums for any Spotify artist  
✅ **Artist Information** - Get detailed artist info (genres, followers, popularity)  
✅ **Related Artists** - Find similar artists based on Spotify's recommendations  
✅ **Audio Features** - Analyze tracks for energy, danceability, tempo, valence, etc.  
✅ **Track Details** - Get complete information about specific tracks  
✅ **Album Details** - View full album information with track listings  
✅ **Batch Audio Analysis** - Get audio features for up to 100 tracks at once  
✅ **Secure Authentication** - Bearer token authentication with middleware  
✅ **Azure Deployment** - Automated CI/CD with GitHub Actions  
✅ **Copilot Studio Ready** - Direct integration with Microsoft Copilot Studio  

---

## 🏗️ Architecture

```
┌─────────────────────┐
│  Copilot Studio     │
│  Agent              │
└──────────┬──────────┘
           │ MCP Protocol
           │ (Streamable HTTP)
           │
┌──────────▼──────────┐
│  Azure Web App      │
│  FastMCP Server     │
│  + Auth Middleware  │
└──────────┬──────────┘
           │ REST API
           │
┌──────────▼──────────┐
│  Spotify Web API    │
└─────────────────────┘
```

---

## 📋 Prerequisites

- Python 3.11+
- Spotify Developer Account
- Azure Account (for deployment)
- Microsoft Copilot Studio (for AI agent integration)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ifiecas/spotify-mcp.git
cd spotify-mcp
```

### 2. Set Up Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Note your **Client ID** and **Client Secret**

### 3. Create Environment Variables

Create a `.env` file in the project root:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
LOCAL_TOKEN=your_secure_token_here
PORT=8000
```

> **Note:** Generate a strong random token for `LOCAL_TOKEN` - this secures your MCP server.

### 4. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run Locally

```bash
python server.py
```

The server will start at `http://localhost:8000/mcp`

---

## ☁️ Deploy to Azure

### Option 1: Automated GitHub Actions (Recommended)

1. **Fork this repository**

2. **Set up Azure Web App:**
   - Create an Azure Web App (Python 3.11)
   - Enable **System Assigned Managed Identity**
   - Note your app name (e.g., `spotify-mcp1611`)

3. **Configure GitHub Secrets:**
   
   Go to your repository → Settings → Secrets and variables → Actions, and add:
   
   - `AZUREAPPSERVICE_CLIENTID`
   - `AZUREAPPSERVICE_TENANTID`
   - `AZUREAPPSERVICE_SUBSCRIPTIONID`
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `LOCAL_TOKEN`

4. **Update Workflow File:**
   
   Edit `.github/workflows/main_spotify-mcp1611.yml`:
   ```yaml
   app-name: your-app-name  # Change this to your Azure Web App name
   ```

5. **Push to main branch** - Automatic deployment will trigger!

### Option 2: Manual Azure CLI Deployment

```bash
az login
az webapp up --name your-app-name --resource-group your-rg --runtime "PYTHON:3.11"
```

### Configure Azure Environment Variables

In Azure Portal → Your Web App → Configuration → Application settings, add:

| Name | Value |
|------|-------|
| `SPOTIFY_CLIENT_ID` | Your Spotify Client ID |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify Client Secret |
| `LOCAL_TOKEN` | Your secure authentication token |
| `PORT` | `8000` |

**Save and restart your Web App.**

---

## 🤖 Integrate with Copilot Studio

### Step 1: Create Custom Connector YAML

Create `spotify-mcp.yaml`:

```yaml
swagger: '2.0'
info:
  title: Spotify MCP
  description: MCP server for Spotify artist data
  version: 1.0.0
host: your-app-name.azurewebsites.net
basePath: /
schemes:
  - https
consumes:
  - application/json
produces:
  - application/json
paths:
  /mcp:
    post:
      summary: Invoke Spotify MCP Server
      x-ms-agentic-protocol: mcp-streamable-1.0
      operationId: InvokeSpotifyMCP
      responses:
        '200':
          description: Success
securityDefinitions:
  api_key:
    type: apiKey
    in: header
    name: Authorization
security:
  - api_key: []
```

### Step 2: Create Custom Connector

1. Go to [Power Apps](https://make.powerapps.com) → **Custom connectors**
2. Click **+ New custom connector** → **Import an OpenAPI file**
3. Upload your `spotify-mcp.yaml`
4. Name it: **Spotify MCP**
5. In **Security** tab:
   - Authentication type: **API Key**
   - Parameter name: `Authorization`
   - Parameter location: `Header`
6. Click **Create connector**

### Step 3: Add to Copilot Studio

1. Open [Copilot Studio](https://copilotstudio.microsoft.com)
2. Create or open your agent
3. Go to **Tools** → **Add a tool** → **New tool** → **Model Context Protocol**
4. Fill in:
   - **Server name:** Spotify MCP
   - **Server description:** Retrieves Spotify artist information, top tracks, and albums
   - **Server URL:** `https://your-app-name.azurewebsites.net/mcp`
   - **Authentication:** API Key
5. Create connection with: `Bearer your_LOCAL_TOKEN`

### Step 4: Test Your Agent

Try these prompts to test all the different tools:

**Artist Search:**
- "Search for Billie Eilish on Spotify"
- "Find the artist Drake"

**Track Search:**
- "Find the song Blinding Lights by The Weeknd"
- "Search for tracks by Post Malone"

**Artist Information:**
- "Tell me about Taylor Swift - what genres does she make?"
- "How many followers does Ariana Grande have?"

**Top Tracks & Albums:**
- "Get top tracks for Taylor Swift"
- "Show me The Weeknd's albums"

**Related Artists:**
- "Find artists similar to Billie Eilish"
- "Who are artists like Drake?"

**Audio Analysis:**
- "What's the tempo and energy of Blinding Lights?" (you'll need the track ID)
- "Analyze the audio features of track 0VjIjW4GlUZAMYd2vXMi3b"
- "Is this track danceable and energetic?"

**Detailed Information:**
- "Get full details for track ID 0VjIjW4GlUZAMYd2vXMi3b"
- "Tell me about the album Midnights"

---

## 💡 Use Cases

With 11 powerful Spotify tools, your Copilot can handle sophisticated music queries:

### 🎯 Music Discovery
- "Find songs similar to Blinding Lights"
- "Who are artists like Billie Eilish?"
- "Search for upbeat dance tracks"

### 📊 Music Analysis
- "What's the energy level and tempo of this track?"
- "Compare the danceability of three different songs"
- "Is this song more acoustic or electronic?"

### 🎤 Artist Research
- "Tell me about Taylor Swift's genre and popularity"
- "How many followers does Drake have?"
- "What are The Weeknd's top 5 songs?"

### 📀 Album Exploration
- "Show me all tracks from the album Midnights"
- "What albums did Ariana Grande release?"
- "Get details about this album"

### 🎵 Track Discovery
- "Find the song Anti-Hero by Taylor Swift"
- "Search for tracks with 'love' in the title"
- "Get a 30-second preview of this song"

### 🔗 Recommendation Chains
Your Copilot can chain multiple tools together:
1. Search for an artist → Get their top track → Analyze its audio features
2. Find an album → Get all tracks → Compare their energy levels
3. Search artist → Find similar artists → Get their top tracks

---

## 🛠️ Available Tools

### 1. `search_artist_by_name`

Search for artists on Spotify by name.

**Parameters:**
- `artist_name` (string): The name of the artist to search for

**Example:**
```json
{
  "artist_name": "Taylor Swift"
}
```

**Returns:** Up to 5 matching artists with their Spotify IDs, images, and popularity scores.

---

### 2. `search_tracks`

Search for tracks on Spotify by name, artist, or both.

**Parameters:**
- `query` (string): Search query (track name, artist, or combination)
- `limit` (integer, optional): Maximum number of results (1-50, default: 10)

**Example:**
```json
{
  "query": "Blinding Lights The Weeknd",
  "limit": 5
}
```

**Returns:** Track search results with names, artists, albums, and preview URLs.

---

### 3. `get_artist_top_tracks`

Get the top tracks for a Spotify artist.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

**Returns:** List of the artist's most popular tracks.

---

### 4. `get_artist_albums`

Get albums for a Spotify artist.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

**Returns:** List of albums (up to 10) with release dates and images.

---

### 5. `get_artist_info`

Get detailed information about a Spotify artist.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

**Returns:** Artist details including:
- Genres
- Popularity score (0-100)
- Follower count
- Artist images
- Spotify URL

---

### 6. `get_related_artists`

Get artists similar to a given artist based on Spotify's recommendation algorithm.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

**Returns:** List of up to 20 similar artists.

---

### 7. `get_track_audio_features`

Get audio analysis features for a track (energy, danceability, tempo, etc.).

**Parameters:**
- `track_id` (string): The Spotify ID of the track

**Example:**
```json
{
  "track_id": "0VjIjW4GlUZAMYd2vXMi3b"
}
```

**Returns:** Audio features including:
- **danceability** (0.0-1.0): How suitable for dancing
- **energy** (0.0-1.0): Intensity and activity
- **key** (0-11): Musical key (0 = C, 1 = C#, etc.)
- **loudness** (dB): Overall loudness
- **mode** (0-1): Major (1) or minor (0)
- **speechiness** (0.0-1.0): Presence of spoken words
- **acousticness** (0.0-1.0): Acoustic vs electric
- **instrumentalness** (0.0-1.0): Vocal vs instrumental
- **liveness** (0.0-1.0): Presence of live audience
- **valence** (0.0-1.0): Musical positivity/happiness
- **tempo** (BPM): Beats per minute
- **duration_ms**: Track length in milliseconds

---

### 8. `get_track_details`

Get detailed information about a specific track.

**Parameters:**
- `track_id` (string): The Spotify ID of the track

**Example:**
```json
{
  "track_id": "0VjIjW4GlUZAMYd2vXMi3b"
}
```

**Returns:** Complete track information including:
- Track name
- Artists
- Album
- Duration
- Popularity score
- Preview URL (30-second clip)
- Explicit content flag
- Available markets

---

### 9. `get_album_details`

Get detailed information about a Spotify album.

**Parameters:**
- `album_id` (string): The Spotify ID of the album

**Example:**
```json
{
  "album_id": "4yP0hdKOZPNshxUOjY0cZj"
}
```

**Returns:** Album details including:
- Album name
- Artists
- Release date
- Total tracks
- Full track listing
- Album images
- Popularity score
- Label and copyright info

---

### 10. `get_multiple_tracks_audio_features`

Get audio features for multiple tracks at once (batch operation).

**Parameters:**
- `track_ids` (string): Comma-separated list of Spotify track IDs (up to 100)

**Example:**
```json
{
  "track_ids": "0VjIjW4GlUZAMYd2vXMi3b,4cOdK2wGLETKBW3PvgPWqT,3n3Ppam7vgaVa1iaRUc9Lp"
}
```

**Returns:** Array of audio features for all requested tracks, useful for comparing multiple songs.

---

### 11. `get_artist_albums` (Enhanced)

Get albums for a Spotify artist with filtering options.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

**Returns:** List of albums with metadata.

---

## 📁 Project Structure

```
spotify-mcp/
├── .github/
│   └── workflows/
│       └── main_spotify-mcp1611.yml  # GitHub Actions deployment
├── server.py                          # Main MCP server
├── requirements.txt                   # Python dependencies
├── .env                               # Environment variables (local)
├── .gitignore                         # Git ignore rules
└── README.md                          # This file
```

---

## 🔒 Security

### Authentication Flow

1. **Client Request** → Includes `Authorization: Bearer <token>` header
2. **Middleware Check** → Validates token against `LOCAL_TOKEN`
3. **If Valid** → Request proceeds to MCP server
4. **If Invalid** → Returns 401 Unauthorized

### Current Implementation (Development/Demo)

The current implementation uses a **simple Bearer token** authentication suitable for:
- ✅ Development and testing
- ✅ Single-tenant deployments
- ✅ Internal corporate use with network isolation
- ✅ Proof of concept demonstrations

**Limitations:**
- ❌ Single shared token for all users
- ❌ No user-specific access control
- ❌ No token expiration
- ❌ No audit logging of user actions

---

## 🔐 Production Security Best Practices

### 1. **Implement OAuth 2.0 / OpenID Connect**

For production, replace the simple Bearer token with proper OAuth:

```python
from fastmcp.server.auth import AzureOAuthProvider

# Use Azure Entra ID (recommended for Microsoft ecosystem)
auth = AzureOAuthProvider(
    tenant_id=os.getenv("AZURE_TENANT_ID"),
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    redirect_uri=os.getenv("OAUTH_REDIRECT_URI"),
    scopes=["openid", "profile", "email"]
)

mcp = FastMCP("spotify-mcp", auth=auth)
```

**Supported Identity Providers:**
- Azure Entra ID (Microsoft 365)
- Google Workspace
- GitHub
- Auth0
- WorkOS
- AWS Cognito

**Benefits:**
- ✅ User-specific authentication
- ✅ Automatic token expiration and refresh
- ✅ Single Sign-On (SSO) support
- ✅ Per-user audit trails

---

### 2. **Use Azure Key Vault for Secrets**

Never store secrets in environment variables in production.

**Setup Azure Key Vault:**

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Connect to Key Vault
credential = DefaultAzureCredential()
vault_url = f"https://{os.getenv('KEY_VAULT_NAME')}.vault.azure.net"
client = SecretClient(vault_url=vault_url, credential=credential)

# Retrieve secrets
SPOTIFY_CLIENT_ID = client.get_secret("SpotifyClientId").value
SPOTIFY_CLIENT_SECRET = client.get_secret("SpotifyClientSecret").value
```

**Configure Azure Web App:**
1. Enable **Managed Identity** on your Web App
2. Grant the Managed Identity access to Key Vault
3. Reference secrets using `@Microsoft.KeyVault(...)` syntax

---

### 3. **Implement Rate Limiting**

Protect against abuse with rate limiting middleware:

```python
from fastmcp.server.middleware import RateLimitMiddleware

mcp.add_middleware(
    RateLimitMiddleware(
        max_requests=100,
        window_seconds=60,
        by_client_id=True  # Rate limit per client
    )
)
```

**Recommended Limits:**
- **Development:** 100 requests/minute per client
- **Production:** 1000 requests/minute per client
- **Public API:** 60 requests/minute per IP address

---

### 4. **Add Request Logging and Audit Trail**

Track all API usage for security and compliance:

```python
from fastmcp.server.middleware import LoggingMiddleware
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit.log'),
        logging.StreamHandler()
    ]
)

class AuditMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        user_id = context.request_context.user_id  # From OAuth
        tool_name = context.params.get("name")
        
        logger.info(f"User {user_id} called tool {tool_name}")
        
        result = await call_next(context)
        return result

mcp.add_middleware(AuditMiddleware())
```

**Log to Azure Application Insights:**
```python
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger.addHandler(AzureLogHandler(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
))
```

---

### 5. **Implement Role-Based Access Control (RBAC)**

Control which users can access which tools:

```python
from fastmcp.server.middleware import Middleware

class RBACMiddleware(Middleware):
    ADMIN_TOOLS = {"get_multiple_tracks_audio_features"}
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        user_roles = context.request_context.user_roles  # From OAuth token
        tool_name = context.params.get("name")
        
        # Restrict admin-only tools
        if tool_name in self.ADMIN_TOOLS and "admin" not in user_roles:
            return ToolResult(
                content=[{"type": "text", "text": "Unauthorized: Admin access required"}]
            )
        
        return await call_next(context)

mcp.add_middleware(RBACMiddleware())
```

---

### 6. **Enable Azure Web App Authentication**

Use Azure's built-in authentication (EasyAuth):

**In Azure Portal:**
1. Go to your Web App → **Authentication**
2. Click **Add identity provider**
3. Choose **Microsoft** (or other provider)
4. Configure:
   - **Restrict access:** Require authentication
   - **Unauthenticated requests:** HTTP 401
   - **Token store:** Enabled

**Benefits:**
- ✅ No code changes needed
- ✅ Authentication handled at platform level
- ✅ Works with Copilot Studio's OAuth flow
- ✅ Automatic token validation

---

### 7. **Use Environment-Based Configuration**

Separate dev/staging/prod configurations:

```python
import os

ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "production":
    # Strict security settings
    REQUIRE_HTTPS = True
    MASK_ERROR_DETAILS = True
    ENABLE_RATE_LIMITING = True
    LOG_LEVEL = "WARNING"
elif ENV == "staging":
    REQUIRE_HTTPS = True
    MASK_ERROR_DETAILS = True
    ENABLE_RATE_LIMITING = False
    LOG_LEVEL = "INFO"
else:  # development
    REQUIRE_HTTPS = False
    MASK_ERROR_DETAILS = False
    ENABLE_RATE_LIMITING = False
    LOG_LEVEL = "DEBUG"

mcp = FastMCP(
    "spotify-mcp",
    mask_error_details=MASK_ERROR_DETAILS
)
```

---

### 8. **Secure Spotify API Credentials**

**Best Practice: Use Service Principal per Environment**

1. Create separate Spotify apps for dev/staging/prod
2. Rotate credentials regularly (every 90 days)
3. Monitor for unusual API usage patterns

**Implement Token Rotation:**

```python
import time
from threading import Lock

class SpotifyTokenManager:
    def __init__(self):
        self.token = None
        self.expiry = 0
        self.lock = Lock()
    
    def get_token(self) -> str:
        with self.lock:
            if time.time() >= self.expiry:
                self.refresh_token()
            return self.token
    
    def refresh_token(self):
        # Get new token from Spotify
        resp = requests.post(...)
        self.token = resp.json()["access_token"]
        self.expiry = time.time() + resp.json()["expires_in"] - 60

token_manager = SpotifyTokenManager()
```

---

### 9. **Enable CORS Properly**

Only allow specific origins in production:

```python
from starlette.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://copilotstudio.microsoft.com",
        "https://your-company-domain.com"
    ],  # Never use ["*"] in production
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 10. **Implement Health Checks and Monitoring**

Add health endpoint for Azure monitoring:

```python
@mcp.custom_route("/health", methods=["GET"])
async def health_check():
    # Check Spotify API connectivity
    token = get_spotify_token()
    if not token:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": "Cannot authenticate with Spotify"}
        )
    
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "2.0.0",
            "tools_count": 11
        }
    )
```

**Configure in Azure:**
- Set Health Check Path: `/health`
- Enable **Application Insights**
- Set up **Alerts** for failures

---

### 11. **Data Privacy and Compliance**

**GDPR Compliance:**
- Log only necessary user information
- Implement data retention policies
- Provide user data export/deletion

**Example Audit Log Cleanup:**
```python
import datetime

def cleanup_old_logs():
    """Delete logs older than 90 days (GDPR requirement)"""
    retention_days = 90
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    # Delete logs older than cutoff_date
```

---

## 🛡️ Security Checklist for Production

### Before Going Live:

- [ ] Replace simple Bearer token with OAuth 2.0
- [ ] Move all secrets to Azure Key Vault
- [ ] Enable Azure Web App Managed Identity
- [ ] Configure Azure Web App Authentication (EasyAuth)
- [ ] Implement rate limiting (100-1000 req/min)
- [ ] Add audit logging with Application Insights
- [ ] Set up RBAC for sensitive tools
- [ ] Enable CORS with specific origins only
- [ ] Add health check endpoint
- [ ] Configure alerts for failures
- [ ] Test token expiration and refresh
- [ ] Implement error masking (`mask_error_details=True`)
- [ ] Set up separate Spotify apps per environment
- [ ] Enable HTTPS only (disable HTTP)
- [ ] Configure Web App firewall rules
- [ ] Set up Azure Monitor dashboards
- [ ] Document incident response procedures
- [ ] Perform security penetration testing
- [ ] Review and sign BAA if handling PHI/PII

---

## 📋 Compliance Considerations

### Data Handling
- **Spotify Data:** Subject to Spotify's Terms of Service
- **User Data:** May require GDPR/CCPA compliance
- **Audit Logs:** Retain for compliance (typically 90 days to 7 years)

### Recommended Policies
1. **Data Retention Policy** - How long to keep logs and cached data
2. **Incident Response Plan** - What to do if security breach occurs
3. **Access Control Policy** - Who can access what tools
4. **API Usage Policy** - Rate limits and acceptable use

---

## 🔗 Security Resources

- [Azure Security Best Practices](https://learn.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)
- [FastMCP Authentication Guide](https://gofastmcp.com/servers/auth/authentication)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Spotify API Terms of Service](https://developer.spotify.com/terms)

---

### Best Practices Summary

✅ **Development:** Simple Bearer token (current implementation)  
✅ **Staging:** OAuth + Key Vault + Rate Limiting  
✅ **Production:** OAuth + Key Vault + Rate Limiting + RBAC + Audit Logging + Monitoring

---

## 🧪 Testing

### Test with curl

```bash
# Initialize session
curl -X POST https://your-app-name.azurewebsites.net/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your_token" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
```

### Test in Copilot Studio

1. Open your agent's **Test** pane
2. Ask: "Search for Drake on Spotify"
3. Check Azure logs for:
   ```
   ✅ Token validation successful
   INFO:mcp.server.lowlevel.server:Processing request of type CallToolRequest
   ```

---

## 📊 Monitoring

### View Azure Logs

```bash
az webapp log tail --name your-app-name --resource-group your-rg
```

Or in Azure Portal:
1. Go to your Web App
2. **Monitoring** → **Log stream**

### Expected Log Output

```
🎵 Spotify MCP Server starting...
   Port: 8000
   Endpoint: /mcp
   Authentication: Bearer token required
   Available Tools: 11
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

When requests come in:
```
✅ Token validation successful
INFO:mcp.server.lowlevel.server:Processing request of type CallToolRequest
```

---

## 🐛 Troubleshooting

### Issue: "Unauthorized" Error

**Cause:** Missing or invalid Bearer token

**Solution:**
1. Check your `LOCAL_TOKEN` in Azure Configuration
2. Verify connection in Copilot Studio uses: `Bearer your_token`
3. Ensure no extra spaces in the token

### Issue: "Spotify authentication failed"

**Cause:** Invalid Spotify credentials

**Solution:**
1. Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in Azure
2. Check credentials in [Spotify Dashboard](https://developer.spotify.com/dashboard)
3. Restart Azure Web App after updating

### Issue: Tools not appearing in Copilot Studio

**Cause:** MCP server not properly connected

**Solution:**
1. Verify server URL is correct
2. Test endpoint with curl
3. Check Azure logs for errors
4. Recreate the connection in Copilot Studio

---

## 🎼 Spotify API Features Used

This MCP server leverages the following Spotify Web API endpoints:

| Endpoint | Tool | Rate Limit |
|----------|------|------------|
| `/search` | `search_artist_by_name`, `search_tracks` | Standard |
| `/artists/{id}` | `get_artist_info` | Standard |
| `/artists/{id}/top-tracks` | `get_artist_top_tracks` | Standard |
| `/artists/{id}/albums` | `get_artist_albums` | Standard |
| `/artists/{id}/related-artists` | `get_related_artists` | Standard |
| `/tracks/{id}` | `get_track_details` | Standard |
| `/albums/{id}` | `get_album_details` | Standard |
| `/audio-features/{id}` | `get_track_audio_features` | Standard |
| `/audio-features?ids=` | `get_multiple_tracks_audio_features` | Standard |

**Note:** All endpoints use Client Credentials flow - no user authentication required.

---

## 🔄 API Rate Limits

- **Spotify API:** Rate limits apply per Client ID
- **Recommendation:** Implement caching for frequently requested data
- **Best Practice:** Use batch endpoints (like `get_multiple_tracks_audio_features`) when possible

---

## 📚 Resources

- [FastMCP Documentation](https://gofastmcp.com/)
- [Spotify Web API Docs](https://developer.spotify.com/documentation/web-api)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Copilot Studio MCP Integration](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-mcp)
- [Azure Web Apps Python Docs](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 👤 Author

**Ivy Fiecas-Borjal**

- GitHub: [@ifiecas](https://github.com/ifiecas)
- LinkedIn: [Connect with me](https://www.linkedin.com/in/ifiecas/)

---

## 🙏 Acknowledgements

- Built with [FastMCP](https://gofastmcp.com/)
- Powered by [Spotify Web API](https://developer.spotify.com/)
- Deployed on [Azure App Service](https://azure.microsoft.com/en-us/products/app-service)
- Integrated with [Microsoft Copilot Studio](https://www.microsoft.com/en-us/microsoft-copilot/microsoft-copilot-studio)


---

## 📺 Tutorial

This project was built following concepts from:
- **How to Build a Python-based Custom HTTP MCP Server and Connect it with Copilot Studio** by Rafsan Huseynov and Maciek Jarka
- Watch: [[https://youtu.be/5gWBoc5Rx3w?si=ps4Q_uqzqOJBz2iG](https://youtu.be/5gWBoc5Rx3w?si=x9QJPjXh6jFTwO_4)]([https://youtu.be/5gWBoc5Rx3w?si=ps4Q_uqzqOJBz2iG](https://youtu.be/5gWBoc5Rx3w?si=x9QJPjXh6jFTwO_4))


