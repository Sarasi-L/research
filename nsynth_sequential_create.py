import os
import random
import librosa
import numpy as np
import soundfile as sf

BASE_DIR = r"D:\My Documents\SLIIT\DS4.1\Research Project\data\nsynth"
OUTPUT_PATH = os.path.join(BASE_DIR, "flute_keyboard_guitar_sequential.wav")
SAMPLE_RATE = 16000

# -----------------------------
# PICK RANDOM FILE BY PREFIX
# -----------------------------
def get_random_file(prefix):
    files = [
        f for f in os.listdir(BASE_DIR)
        if f.startswith(prefix) and f.endswith(".wav")
    ]
    return os.path.join(BASE_DIR, random.choice(files))

flute_file = get_random_file("flute")
keyboard_file = get_random_file("keyboard")
guitar_file = get_random_file("guitar")

print("Selected files:")
print(flute_file)
print(keyboard_file)
print(guitar_file)

# -----------------------------
# LOAD AUDIO
# -----------------------------
def load_audio(path):
    audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return audio

flute = load_audio(flute_file)
keyboard = load_audio(keyboard_file)
guitar = load_audio(guitar_file)

# -----------------------------
# SEQUENTIAL CONCATENATION
# -----------------------------
sequential_audio = np.concatenate([flute, keyboard, guitar])

# Normalize
sequential_audio /= np.max(np.abs(sequential_audio))

sf.write(OUTPUT_PATH, sequential_audio, SAMPLE_RATE)

print("✅ Sequential audio generated:")
print(OUTPUT_PATH)
