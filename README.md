# 🎵 Spotify MCP Server

A **Model Context Protocol (MCP)** server that connects to the Spotify Web API, enabling AI agents in Microsoft Copilot Studio to search for artists, retrieve top tracks, and get album information.

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/)

---

## 🌟 Features

✅ **Search Artists** - Find artists on Spotify by name  
✅ **Get Top Tracks** - Retrieve an artist's most popular tracks  
✅ **Get Albums** - List albums for any Spotify artist  
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
git clone https://github.com/yourusername/spotify-mcp.git
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

Try these prompts:
- "Search for Billie Eilish on Spotify"
- "Get top tracks for Taylor Swift"
- "Show me The Weeknd's albums"

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

### 2. `get_artist_top_tracks`

Get the top tracks for a Spotify artist.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

### 3. `get_artist_albums`

Get albums for a Spotify artist.

**Parameters:**
- `artist_id` (string): The Spotify ID of the artist

**Example:**
```json
{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}
```

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

### Best Practices

- ✅ Never commit `.env` file to Git
- ✅ Use strong, random tokens for `LOCAL_TOKEN`
- ✅ Rotate tokens periodically
- ✅ Use Azure Key Vault for production secrets
- ✅ Enable HTTPS only (enforced by Azure)

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

## 🔄 API Rate Limits

- **Spotify API:** Rate limits apply per Client ID
- **Best Practice:** Implement caching for frequently requested data

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

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ivy Fiecas-Borjal**

- GitHub: [@yourusername](https://github.com/yourusername)

---

## 🙏 Acknowledgements

- Built with [FastMCP](https://gofastmcp.com/)
- Powered by [Spotify Web API](https://developer.spotify.com/)
- Deployed on [Azure App Service](https://azure.microsoft.com/en-us/products/app-service)
- Integrated with [Microsoft Copilot Studio](https://www.microsoft.com/en-us/microsoft-copilot/microsoft-copilot-studio)

---
