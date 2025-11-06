# spotify-mcp
Spotify MCP Server -- A Model Context Protocol (MCP) server that retrieves an artist’s top tracks from Spotify, enriches them with audio features (energy, valence, tempo, etc.), and returns clean, AI-ready JSON output.

🎵 Spotify MCP Server

A Model Context Protocol (MCP) server that connects to the Spotify Web API to retrieve an artist’s top tracks, enriches them with audio features (energy, danceability, valence, tempo, etc.), and returns clean, AI-ready JSON output — perfect for Copilot Studio, Azure AI Foundry, or other MCP-compatible environments.

🧩 What This Project Does

Fetches top tracks for any artist using their Spotify Artist ID

Retrieves each track’s audio analysis (energy, valence, tempo, etc.)

Returns a structured JSON response (summary + track-level details)

Designed to run as an MCP server compatible with OpenAI’s or Anthropic’s clients

Ready for extension to Azure Blob Storage, AI embeddings, or Copilot Studio integration

🚀 Features

✅ Clean JSON output
✅ Secure .env configuration (no credentials in code)
✅ Works directly with MCP Inspector
✅ Easily extendable to Azure services
✅ Built with Python 3.10+

🧱 Project Structure
spotify-mcp/
├── server.py          # Main MCP server script
├── .env               # Spotify API credentials (excluded from Git)
├── .gitignore         # Ignores secrets and local files
├── requirements.txt   # Python dependencies
└── README.md          # This file

⚙️ Requirements

Python 3.10 or higher

Spotify Developer account
→ Create at https://developer.spotify.com/dashboard

Registered Spotify app (to get Client ID & Client Secret)

🔧 Setup

Clone the repo

git clone https://github.com/yourusername/spotify-mcp.git
cd spotify-mcp


Create a virtual environment

python3 -m venv .venv
source .venv/bin/activate


Install dependencies

pip install -r requirements.txt


Create a .env file in the project root

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret


Run the MCP server

mcp dev server.py


This opens the MCP Inspector in your browser:
http://localhost:6274

🧠 Example MCP Tool Invocation

You can call the tool in the Inspector using:

{
  "artist_id": "06HL4z0CvFAxyc27GXpf02"
}


Output:

{
  "artist": {
    "id": "06HL4z0CvFAxyc27GXpf02",
    "name": "Taylor Swift",
    "average_audio_profile": {
      "energy": 0.73,
      "valence": 0.56,
      "danceability": 0.62
    },
    "track_count": 10
  },
  "tracks": [
    {
      "track_name": "Opalite",
      "album": "The Life of a Showgirl",
      "release_date": "2025-10-03",
      "popularity": 97,
      "spotify_url": "https://open.spotify.com/track/3yWuTOYDztXjZxdE2cIRUa",
      "audio_features": {
        "danceability": 0.54,
        "energy": 0.79,
        "valence": 0.49,
        "instrumentalness": 0.001,
        "tempo_bpm": 134.7
      }
    }
  ]
}

🧩 Extending the Project

You can easily add:

Azure Blob Storage → upload each JSON response automatically

@tool("get_artist_summary") → compute mood trends, averages, or embeddings

Azure AI Search → make track data queryable from Copilot Studio

🧰 Troubleshooting
Issue	Possible Fix
400 Bad Request from Spotify	Check if your Client ID/Secret are valid and in .env
403 Forbidden	Make sure you’re using the Client Credentials flow, not OAuth
MCP Inspector doesn’t load	Run mcp dev server.py inside the virtual environment
🧾 License

MIT License © 2025 Ivy Fiecas-Borjal

✨ Acknowledgements

Built with ❤️ by Ivy Fiecas-Borjal

Powered by Spotify Web API
 and Model Context Protocol
