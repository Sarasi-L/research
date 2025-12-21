import librosa
import numpy as np

from backend.services.monophonic.preprocess_audio import preprocess_audio


def validate_preprocessing(raw_path, instrument):
    raw, sr = librosa.load(raw_path, sr=16000, mono=True)
    clean, _ = preprocess_audio(raw_path, instrument)

    return {
        "raw_duration_sec": len(raw) / sr,
        "clean_duration_sec": len(clean) / sr,
        "raw_energy": float(np.mean(raw ** 2)),
        "clean_energy": float(np.mean(clean ** 2)),
        "silence_removed": len(clean) < len(raw),
    }
