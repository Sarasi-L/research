# backend/preprocess_separated.py
import librosa
import librosa.display
import matplotlib.pyplot as plt
from pathlib import Path

def generate_spectrogram(input_file: str, output_file: str):
    try:
        y, sr = librosa.load(input_file, sr=44100)
        print(f"[INFO] Loaded {input_file} for spectrogram | Shape: {y.shape}, SR: {sr}")

        S = librosa.stft(y)
        S_db = librosa.amplitude_to_db(abs(S))
        
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz')
        plt.colorbar(format='%+2.0f dB')
        plt.title(f"Spectrogram: {Path(input_file).stem}")
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        print(f"[INFO] Spectrogram saved: {output_file}")

        # Verification: try reloading the image
        import matplotlib.image as mpimg
        img = mpimg.imread(output_file)
        assert img.shape[0] > 0
        print(f"[INFO] Verification passed: Spectrogram image shape {img.shape}")
    except Exception as e:
        print(f"[ERROR] Spectrogram generation failed: {e}")

# Run standalone for testing
if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]  # e.g., backend/separated/drums.wav
    output_file = sys.argv[2] # e.g., backend/preprocessed/drums.png
    generate_spectrogram(input_file, output_file)
