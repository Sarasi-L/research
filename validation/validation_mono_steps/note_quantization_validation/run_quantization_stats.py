import os
import librosa
import numpy as np

from backend.services.monophonic.note_quantization import quantize_notes
from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes, smooth_note_durations

# -----------------------------
# DATA
# -----------------------------
AUDIO_DIR = r"D:\My Documents\SLIIT\DS4.1\Research Project\data\dataset nsynth"
MAX_FILES = 30
TEMPO = 120

raw_beats = []
quantized_beats = []
duration_names = []
tie_flags = []

processed = 0

for fname in sorted(os.listdir(AUDIO_DIR)):
    if processed >= MAX_FILES:
        break
    if not fname.endswith(".wav"):
        continue

    y, sr = librosa.load(os.path.join(AUDIO_DIR, fname), sr=22050)

    time, freq, conf = extract_pitch(y, sr)

    notes = smooth_note_durations(
        frames_to_notes(time, freq, conf, instrument="voice")
    )

    quantized = quantize_notes(notes, TEMPO)

    for q in quantized:
        raw_beats.append(q["duration_beats"])
        quantized_beats.append(q["quantized_beats"])
        duration_names.append(q["duration_name"])
        tie_flags.append(q["duration_name"] == "tied")

    processed += 1

print("\n===== QUANTIZATION STATISTICS =====")
print(f"Files processed : {processed}")
print(f"Notes analysed  : {len(raw_beats)}")
