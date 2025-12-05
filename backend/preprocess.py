# backend/preprocess.py
import librosa
import soundfile as sf
from pathlib import Path

def preprocess_audio(input_file: str, output_file: str, target_sr=44100):
    try:
        y, sr = librosa.load(input_file, sr=target_sr, mono=False)
        print(f"[INFO] Loaded {input_file} | Original SR: {sr}, Shape: {y.shape}")

        # Normalize audio
        y = y / max(abs(y.max()), abs(y.min()), 1e-6)
        sf.write(output_file, y.T, target_sr)
        print(f"[INFO] Preprocessed audio saved: {output_file}")

        # Verification: check if file saved correctly
        y_check, sr_check = librosa.load(output_file, sr=None, mono=False)
        assert y_check.shape[0] > 0
        print(f"[INFO] Verification passed: {output_file} loaded successfully with shape {y_check.shape}")
    except Exception as e:
        print(f"[ERROR] Preprocessing failed: {e}")

# Run standalone for testing
if __name__ == "__main__":
    import sys
    input_path = sys.argv[1]  # e.g., backend/audio_input/mixed_song.wav
    output_path = sys.argv[2] # e.g., backend/preprocessed/mixed_song.wav
    preprocess_audio(input_path, output_path)
