#backend/services/monophonic/preprocess_monophonic_audio.py

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


def preprocess_audio(input_file: str, sr=22050):
    """
    Load audio, convert to mono, normalize
    Returns waveform + sample rate
    """
    y, sr = librosa.load(input_file, sr=sr, mono=True)

    # Normalize
    y = y / max(np.max(np.abs(y)), 1e-6)

    return y, sr

