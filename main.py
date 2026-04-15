from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import librosa
import tempfile
import requests
import base64

# -----------------------
# Create the FastAPI app
# -----------------------
app = FastAPI()

# -----------------------
# Step 1: CORS middleware
# This goes immediately after creating the app
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # allow all domains for now
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

def map_tempo_to_queries(tempo):
    if tempo < 80:
        return ["ambient chill", "lofi beats", "sad indie", "sleep music"]

    elif tempo < 100:
        return ["indie pop", "bedroom pop", "alt r&b", "chill vibes"]

    elif tempo < 120:
        return ["pop hits", "dance pop", "indie rock", "feel good music"]

    elif tempo < 140:
        return ["house music", "electronic dance", "party songs", "club hits"]

    else:
        return ["workout hype", "trap", "edm festival", "gym motivation"]

# -----------------------------
# Helper function: search Spotify playlists
# -----------------------------
def search_playlists(queries):
    token = get_spotify_token()
    if not token:
        return []

    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}

    playlists = []

    for query in queries:
        params = {"q": query, "type": "playlist", "limit": 2}

        try:
            res = requests.get(url, headers=headers, params=params)
            data = res.json()

            for item in data.get("playlists", {}).get("items", []):
                if item and item.get("external_urls"):
                    playlists.append({
                        "name": item.get("name"),
                        "url": item["external_urls"].get("spotify")
                    })

        except Exception as e:
            print("Spotify error:", e)

    return playlists

# -----------------------------
# Endpoint: analyze uploaded audio
# -----------------------------
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            tempo = get_tempo(tmp_path)
        except Exception as e:
            print("Tempo error:", e)
            tempo = 100  # fallback

        queries = map_tempo_to_queries(tempo)

        try:
            playlists = search_playlists(queries)
        except Exception as e:
            print("Spotify error:", e)
            playlists = []

        return {"tempo": tempo, "query": query, "playlists": [10] playlists}

    except Exception as e:
        print("❌ CRASH:", e)
        return {"error": str(e)}

# -----------------------------
# Endpoint: test server
# -----------------------------
@app.get("/")
def test():
    return {"message": "working"}
