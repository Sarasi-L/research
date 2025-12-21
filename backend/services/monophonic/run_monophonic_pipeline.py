#backend/services/monophonic/run_monophonic_pipline.py

from services.monophonic.preprocess_audio import preprocess_audio
from services.monophonic.pitch_extraction import extract_pitch
import numpy as np


def run_monophonic_pipeline(audio_path: str, instrument: str):
    """
    Full monophonic pipeline:
    preprocess → pitch extraction
    """

    print("[INFO] Running monophonic preprocessing...")
    y, sr = preprocess_audio(audio_path, instrument)

    print("[INFO] Extracting pitch using CREPE...")
    time, frequency, confidence = extract_pitch(y, sr)

    # Convert numpy → JSON safe
    pitch_data = [
        {
            "time": float(t),
            "frequency": float(f) if not np.isnan(f) else None,
            "confidence": float(c)
        }
        for t, f, c in zip(time, frequency, confidence)
        if c > 0.5 and not np.isnan(f)
    ]

    print(f"[INFO] Extracted {len(pitch_data)} pitch points")

    return {
        "sample_rate": sr,
        "pitch_points": pitch_data[:300]  # limit for frontend safety
    }
