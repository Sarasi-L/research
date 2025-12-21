# backend/app.py
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

# FIXED: Mount the STEMS directory, not temp!
BASE_DIR = Path(__file__).resolve().parent
STEMS_DIR = BASE_DIR / "stems"
UPLOAD_DIR = BASE_DIR / "uploads"

# Create directories if they don't exist
STEMS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

print(f"[INFO] Stems directory: {STEMS_DIR.absolute()}")
print(f"[INFO] Stems directory exists: {STEMS_DIR.exists()}")
print(f"[INFO] Uploads directory: {UPLOAD_DIR.absolute()}")

# Mount stems directory so frontend can access the audio files
app.mount("/stems", StaticFiles(directory=str(STEMS_DIR)), name="stems")

# Include router
app.include_router(upload_router)

@app.get("/")
async def root():
    return {"message": "Music Separator API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)