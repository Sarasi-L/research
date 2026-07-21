#backend/services/preprocess_stereo_audio.py

import librosa
import soundfile as sf
import numpy as np

def preprocess_audio(input_file: str, output_file: str, sr=22050):
    
    y, original_sr = librosa.load(input_file, sr=sr, mono=False)
    
    # (channels, samples) or (samples,) if mono
    if y.ndim == 1:
        y = np.expand_dims(y, axis=0)  
    
    # Normalize per channel
    y = y / np.maximum(np.max(np.abs(y), axis=1, keepdims=True), 1e-6)
    
    sf.write(output_file, y.T, sr)  
    return output_file
