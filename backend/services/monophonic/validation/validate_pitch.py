import numpy as np
from backend.services.monophonic.pitch_extraction import extract_pitch




def validate_pitch(y, sr):
    t, f0, conf = extract_pitch(y, sr)


    voiced_ratio = np.sum(~np.isnan(f0)) / len(f0)
    pitch_std = np.nanstd(f0)


    return {
        "voiced_frame_ratio": float(voiced_ratio),
        "pitch_std_hz": float(pitch_std),
        "mean_confidence": float(np.nanmean(conf))
}