# backend/services/separate_demucs.py

from pathlib import Path
import torch
import torchaudio
import soundfile as sf

from demucs.pretrained import get_model
from demucs.apply import apply_model

from services.utils.env_fix import fix_windows_conda

# Fix DLL issue (Windows + Conda)
fix_windows_conda()

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "models" / "htdemucs" / "htdemucs.th"

# Cache the model globally to avoid reloading
_cached_model = None

def get_cached_model():
    """Load model once and cache it"""
    global _cached_model
    if _cached_model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Demucs model not found at {MODEL_PATH}")
        
        print("[INFO] Loading Demucs model (first time only)...")
        model = get_model("htdemucs")
        state = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        model.load_state_dict(state)
        model.eval()
        
        # Use GPU if available
        if torch.cuda.is_available():
            model = model.cuda()
            print("[INFO] Using GPU acceleration")
        else:
            print("[INFO] Using CPU (slower)")
        
        _cached_model = model
    
    return _cached_model


def separate_polyphonic(input_file: str, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use cached model
    model = get_cached_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load audio
    wav, sr = torchaudio.load(input_file)
    
    print(f"[INFO] Loaded audio: {wav.shape} channels, {sr} Hz")

    # CRITICAL FIX: Convert mono to stereo if needed
    if wav.shape[0] == 1:
        print("[INFO] Converting mono to stereo...")
        wav = wav.repeat(2, 1)  # Duplicate mono channel to create stereo
    
    # Ensure we have exactly 2 channels (stereo)
    if wav.shape[0] > 2:
        print(f"[WARNING] Audio has {wav.shape[0]} channels, using first 2")
        wav = wav[:2, :]
    
    print(f"[INFO] Audio shape after channel fix: {wav.shape}")

    # Resample if needed
    if sr != model.samplerate:
        print(f"[INFO] Resampling from {sr} Hz to {model.samplerate} Hz")
        wav = torchaudio.transforms.Resample(sr, model.samplerate)(wav)

    # Move to GPU if available
    wav = wav.to(device)

    # Add batch dimension
    wav = wav.unsqueeze(0)
    
    print(f"[INFO] Final input shape: {wav.shape} (batch, channels, samples)")

    # Apply Demucs with optimizations
    with torch.no_grad():  # Disable gradient computation for inference
        stems = apply_model(
            model, 
            wav,
            shifts=1,      # Reduced from default 10 (faster but slightly less quality)
            overlap=0.25,  # Default, you can reduce to 0.1 for more speed
            split=True     # Process in chunks to save memory
        )

    print(f"[INFO] Separation complete, output shape: {stems.shape}")

    # Save stems
    stem_paths = {}
    for i, name in enumerate(model.sources):
        out_file = output_dir / f"{name}.wav"
        
        # Get stem audio (remove batch dimension, move to CPU)
        stem_audio = stems[0, i].cpu().numpy().T
        
        print(f"[INFO] Saving {name} stem: {stem_audio.shape}")
        
        sf.write(
            out_file,
            stem_audio,
            model.samplerate
        )
        stem_paths[name] = str(out_file)
        print(f"[INFO] ✓ Saved {name} to {out_file}")

    return stem_paths