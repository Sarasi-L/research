#backend/services/preprocess.py
import librosa
import soundfile as sf
import numpy as np

def preprocess_audio(input_file: str, output_file: str, sr=22050):
    # Load in original channels
    y, original_sr = librosa.load(input_file, sr=sr, mono=False)
    
    # y shape: (channels, samples) or (samples,) if mono
    if y.ndim == 1:
        y = np.expand_dims(y, axis=0)  # make it (1, samples)
    
    # Normalize per channel
    y = y / np.maximum(np.max(np.abs(y), axis=1, keepdims=True), 1e-6)
    
    sf.write(output_file, y.T, sr)  # sf.write expects (samples, channels)
    return output_file
