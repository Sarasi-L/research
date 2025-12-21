#backend/services/monophonic/preprocess_audio.py

import librosa
import numpy as np
from scipy.signal import butter, filtfilt
from .instrument_ranges import INSTRUMENT_FREQ_RANGES




def bandpass_filter(y, sr, low, high, order=4):
    nyq = 0.5 * sr
    low /= nyq
    high /= nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, y)




def preprocess_audio(audio_path: str, instrument: str):
# Load audio
    y, sr = librosa.load(audio_path, sr=16000, mono=True)


# Normalize
    y = y / np.max(np.abs(y))


# Trim silence
    y, _ = librosa.effects.trim(y, top_db=25)


# Instrument‑aware band‑pass
    if instrument in INSTRUMENT_FREQ_RANGES:
        low, high = INSTRUMENT_FREQ_RANGES[instrument]
        y = bandpass_filter(y, sr, low, high)


    return y, sr