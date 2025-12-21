# backend/routers/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path

from services.detect_instruments import detect_all_instruments
from services.detect_monophonic_instrument import detect_single_instrument
from services.monophonic.note_segmentation import frames_to_notes
from services.separate_demucs import separate_polyphonic
from services.detect_type import detect_type
from services.monophonic.run_monophonic_pipeline import run_monophonic_pipeline
from services.monophonic.tempo_beat_estimation import estimate_tempo_and_beats


router = APIRouter()

UPLOAD_DIR = Path("uploads")
STEMS_DIR = Path("stems")
UPLOAD_DIR.mkdir(exist_ok=True)
STEMS_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio, detect type, and process accordingly"""
    
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[INFO] File uploaded: {file_path}")
        
        # Detect audio type
        print("[INFO] Detecting audio type...")
        audio_type, confidence = detect_type(str(file_path))
        print(f"[INFO] Detected type: {audio_type} ({confidence*100:.1f}% confidence)")
        
        # Decision: Monophonic or Polyphonic?
        if audio_type == "monophonic":
            print("[INFO] Monophonic audio detected - skipping stem separation")
            
            # Detect the single instrument directly
            instrument_data = detect_single_instrument(str(file_path))
            instrument_name = instrument_data.get("instrument", "unknown")

            # Run monophonic preprocessing + pitch extraction
            pitch_result = run_monophonic_pipeline(
                audio_path=str(file_path),
                instrument=instrument_name
            )

            # Convert pitch frames to note segments
            import numpy as np
            times = np.array([p["time"] for p in pitch_result["pitch_points"]])
            freqs = np.array([p["frequency"] for p in pitch_result["pitch_points"]])
            confs = np.array([p["confidence"] for p in pitch_result["pitch_points"]])
            note_segments = frames_to_notes(times, freqs, confs)
            tempo_data = estimate_tempo_and_beats(str(file_path))


            return JSONResponse({
                "message": "Monophonic audio detected",
                "type": audio_type,
                "confidence": float(confidence),
                "is_monophonic": True,
                "instrument": instrument_data,
                "pitch_data": pitch_result,
                "note_data": {"notes": note_segments},
                "tempo_data": tempo_data,
                "audio_file": f"/uploads/{file.filename}"
            })

        
        else:  # Polyphonic
            print("[INFO] Polyphonic audio detected - separating stems with Demucs...")
            
            # Separate stems using Demucs
            stem_paths = separate_polyphonic(str(file_path), output_dir=str(STEMS_DIR))
            print(f"[INFO] Stems separated: {list(stem_paths.keys())}")
            
            # Detect instruments in each stem
            print("[INFO] Detecting instruments in stems...")
            instruments = detect_all_instruments(stem_paths)
            
            # Create response with relative URLs
            stems_response = {
                name: f"/stems/{Path(path).name}" 
                for name, path in stem_paths.items()
            }
            
            return JSONResponse({
                "message": "Processing complete",
                "type": audio_type,
                "confidence": float(confidence),
                "is_monophonic": False,
                "stems": stems_response,
                "instruments": instruments
            })
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
