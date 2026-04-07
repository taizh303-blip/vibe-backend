from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import librosa
import tempfile
import requests
import base64

# -----------------------------
# Create FastAPI app
# -----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allows all origins, including Framer Desktop
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------
# Spotify credentials
# Replace with your own values from Spotify Developer Dashboard
# -----------------------------
SPOTIFY_CLIENT_ID = "fd55177b6eef479fa575364afa999ee7"
SPOTIFY_CLIENT_SECRET = "e39a9079abca453b9223074222c8c34f"

# -----------------------------
# Helper function: get Spotify token automatically
# -----------------------------
def get_spotify_token():
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}
    data = {"grant_type": "client_credentials"}

    res = requests.post(auth_url, headers=headers, data=data)
    res.raise_for_status()  # will raise an error if request fails
    token = res.json()["access_token"]
    return token

# -----------------------------
# Helper function: tempo analysis
# -----------------------------
def get_tempo(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # ✅ ensure it's a normal float
    if hasattr(tempo, "__len__"):
        tempo = tempo[0]

    return float(tempo)

def map_tempo_to_query(tempo):
    if tempo < 90:
        return "chill ambient"
    elif tempo < 120:
        return "indie pop"
    else:
        return "workout hype"

# -----------------------------
# Helper function: search Spotify playlists
# -----------------------------
def search_playlists(query):
    token = get_spotify_token()

    # ✅ ADD THIS CHECK RIGHT HERE
    if not token:
        print("❌ Failed to get Spotify token")
        return []

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": "playlist", "limit": 5}

    res = requests.get(url, headers=headers, params=params)
    print("Spotify status:", res.status_code)
    data = res.json()
    print("Spotify response:", data)

    playlists = []

    for item in data.get("playlists", {}).get("items", []):
        if item and item.get("external_urls"):
            playlists.append({
                "name": item.get("name", "Unknown"),
                "url": item["external_urls"].get("spotify", "#")
            })

    return playlists

# -----------------------------
# Endpoint: analyze uploaded audio
# -----------------------------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        print("🔥 Analyze endpoint hit")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            tempo = get_tempo(tmp_path)
        except Exception as e:
            print("Tempo error:", e)
            tempo = 100  # fallback

        query = map_tempo_to_query(tempo)

        try:
            playlists = search_playlists(query)
        except Exception as e:
            print("Spotify error:", e)
            playlists = []

        print("✅ Returning response")

        return {
            "tempo": tempo,
            "query": query,
            "playlists": playlists
        }

    except Exception as e:
        print("❌ CRASH:", e)
        return {"error": str(e)}
    }

# -----------------------------
# Endpoint: test server
# -----------------------------
@app.get("/")
def test():
    return {"message": "working"}
