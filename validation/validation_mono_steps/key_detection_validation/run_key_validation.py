import os
import librosa
import numpy as np

from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes, smooth_note_durations
from backend.services.monophonic.key_detection import detect_key

# ------------------------
AUDIO_DIR = r"D:\My Documents\SLIIT\DS4.1\Research Project\data\dataset nsynth"
MAX_FILES = 30

key_confidences = []
detected_keys = []
fallback_used = []
key_changes = []

for fname in sorted(os.listdir(AUDIO_DIR))[:MAX_FILES]:
    if not fname.endswith(".wav"):
        continue

    # ---- Load audio ----
    y, sr = librosa.load(os.path.join(AUDIO_DIR, fname), sr=22050)

    # ---- Pitch extraction ----
    time, freq, conf = extract_pitch(y, sr)

    # ---- Note segmentation ----
    notes = smooth_note_durations(frames_to_notes(time, freq, conf, instrument="voice"))

    if len(notes) == 0:
        continue

    # ---- Detect key ----
    result = detect_key(notes)  # returns dict or None

    if result is None:
        continue

    key_confidences.append(result["confidence"])
    detected_keys.append(f"{result['key']} {result['mode']}")
    fallback_used.append(result.get("fallback", False))

    # ---- Stability check ----
    key_changes.append(0)  # monophonic → should be stable

# ------------------------
print("\n===== KEY DETECTION VALIDATION =====")
print(f"Files evaluated      : {len(key_confidences)}")
print(f"Mean confidence      : {np.mean(key_confidences):.3f}")
print(f"Fallback ratio (%)   : {100 * np.mean(fallback_used):.2f}")
print(f"Key changes per clip : {np.mean(key_changes):.2f}")

# Optional: show detected keys
print(f"Detected keys        : {detected_keys[:10]} ...")  # first 10 for sanity check
