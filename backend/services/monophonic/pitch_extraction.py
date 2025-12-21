#backend/services/monophonic/pitch_extraction.py

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


# Confidence filtering
    mask = confidence > 0.5
    frequency[~mask] = np.nan


# Smooth pitch curve
    frequency = medfilt(frequency, kernel_size=5)


    return time, frequency, confidence