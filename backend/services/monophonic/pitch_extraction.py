# backend/services/monophonic/pitch_extraction.py

import crepe
import numpy as np
from scipy.signal import medfilt


def extract_pitch(y, sr, model_capacity="medium"):
    time, frequency, confidence, _ = crepe.predict(
        y,
        sr,
        model_capacity=model_capacity,
        step_size=10,
        viterbi=True
    )

    # --- FIX: Confidence mask produces NaNs, NOT zeros ---
    # Previously: frequency[~mask] = np.nan → medfilt smears NaN/0 into real pitches
    mask = confidence > 0.5
    frequency[~mask] = np.nan

    # --- FIX: Interpolate NaNs BEFORE median filtering ---
    # medfilt on NaN-containing arrays corrupts boundaries
    nan_mask = np.isnan(frequency)
    if np.any(~nan_mask):  # at least some valid frames exist
        valid_idx = np.where(~nan_mask)[0]
        invalid_idx = np.where(nan_mask)[0]
        frequency[invalid_idx] = np.interp(
            invalid_idx,
            valid_idx,
            frequency[valid_idx]
        )

    # --- FIX: Smaller kernel (5 was too aggressive, blurs note transitions) ---
    frequency = medfilt(frequency, kernel_size=3)

    # Re-apply NaN mask after smoothing so downstream code
    # still knows which frames were unconfident
    frequency[~mask] = np.nan

    return time, frequency, confidence
