# root backend/services/polyphonic/separate_demucs.py

from pathlib import Path
import torch
import torchaudio
import soundfile as sf

from demucs.pretrained import get_model
from demucs.apply import apply_model

from services.utils.env_fix import fix_windows_conda


# Fix DLL issue (Windows + Conda)
fix_windows_conda()

BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "models" / "htdemucs" / "htdemucs.th"


_cached_model = None

def get_cached_model():
    
    global _cached_model
    if _cached_model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Demucs model not found at {MODEL_PATH}")
        
        print("[INFO] Loading Demucs model (first time only)...")
        model = get_model("htdemucs")
        state = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
        model.load_state_dict(state)
        model.eval()
        
        
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

    
    model = get_cached_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    
    wav, sr = torchaudio.load(input_file)
    
    print(f"[INFO] Loaded audio: {wav.shape} channels, {sr} Hz")

    if wav.shape[0] == 1:
        print("[INFO] Converting mono to stereo...")
        wav = wav.repeat(2, 1)  
    
    
    if wav.shape[0] > 2:
        print(f"[WARNING] Audio has {wav.shape[0]} channels, using first 2")
        wav = wav[:2, :]
    
    print(f"[INFO] Audio shape after channel fix: {wav.shape}")

    
    if sr != model.samplerate:
        print(f"[INFO] Resampling from {sr} Hz to {model.samplerate} Hz")
        wav = torchaudio.transforms.Resample(sr, model.samplerate)(wav)

    
    wav = wav.to(device)

    # Add batch dimension
    wav = wav.unsqueeze(0)
    
    print(f"[INFO] Final input shape: {wav.shape} (batch, channels, samples)")

    
    with torch.no_grad():  
        stems = apply_model(
            model, 
            wav,
            shifts=1,      
            overlap=0.25,  
            split=True     
        )

    print(f"[INFO] Separation complete, output shape: {stems.shape}")

    
    stem_paths = {}
    for i, name in enumerate(model.sources):
        out_file = output_dir / f"{name}.wav"
        
        
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