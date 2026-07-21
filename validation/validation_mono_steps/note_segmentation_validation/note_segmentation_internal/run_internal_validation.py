# validate/note_segmentation_validation/note_segmentation_internal/run_internal_validation.py

import os
import librosa
import numpy as np

from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import (
    frames_to_notes,
    smooth_note_durations
)
from validation.note_segmentation_validation.note_segmentation_internal.internal_metrics import (
    compute_note_metrics
)

AUDIO_DIR = r"D:\My Documents\SLIIT\DS4.1\Research Project\data\dataset"
MAX_FILES = 100

pitch_stds = []
purities = []
durations = []
notes_per_clip = []

files = sorted([f for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")])

for i, fname in enumerate(files[:MAX_FILES]):
    print(f"Processing {i+1}/{MAX_FILES}: {fname}")

    y, sr = librosa.load(os.path.join(AUDIO_DIR, fname), sr=22050)

    time, freq, conf = extract_pitch(y, sr)

    notes = smooth_note_durations(
        frames_to_notes(time, freq, conf)
    )

    clip_metrics = []

    for n in notes:
        m = compute_note_metrics(n, time, freq)
        if m:
            pitch_stds.append(m["pitch_std"])
            purities.append(m["purity"])
            durations.append(m["duration"])
            clip_metrics.append(m)

    if len(notes) > 0:
        notes_per_clip.append(len(notes))

# -------- REPORT --------
print("\n===== INTERNAL NOTE SEGMENTATION VALIDATION =====")
print(f"Files evaluated          : {len(notes_per_clip)}")
print(f"Mean pitch std (Hz)      : {np.mean(pitch_stds):.2f}")
print(f"Mean purity (%)          : {np.mean(purities)*100:.2f}")
print(f"Mean note duration (s)   : {np.mean(durations):.2f}")
print(f"Notes per clip           : {np.mean(notes_per_clip):.2f}")
