from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers.upload import router as upload_router
from pathlib import Path

app = FastAPI(title="Music Notation ML Pipeline")

# CORS middleware - allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = Path(__file__).resolve().parent

STEMS_DIR = BASE_DIR / "stems"
UPLOAD_DIR = BASE_DIR / "uploads"
MUSICXML_DIR = BASE_DIR / "musicxml"

# Create directories if they don't exist
STEMS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MUSICXML_DIR.mkdir(parents=True, exist_ok=True)

print(f"[INFO] Stems directory: {STEMS_DIR.absolute()}")
print(f"[INFO] Stems directory exists: {STEMS_DIR.exists()}")
print(f"[INFO] Uploads directory: {UPLOAD_DIR.absolute()}")
print(f"[INFO] MusicXML directory: {MUSICXML_DIR.absolute()}")

# Mount stems + uploads via StaticFiles (audio files are fine as static)
app.mount("/stems", StaticFiles(directory=str(STEMS_DIR)), name="stems")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# NOTE: /musicxml is NOT mounted as StaticFiles
# It is handled by the router in routers/upload.py with correct Content-Type headers
# Mounting it here as StaticFiles would intercept requests before the router and
# serve files with wrong content-type, breaking OpenSheetMusicDisplay rendering.

# Include router (this handles /musicxml/{filename} with proper headers)
app.include_router(upload_router)

@app.get("/")
async def root():
    return {"message": "Music Separator API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)