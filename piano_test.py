from backend.services.polyphonic.separate_demucs import separate_polyphonic
from backend.services.polyphonic.detect_piano_from_stems import detect_piano_from_stems

import os

# input song (in project root)
audio_file = "polysong.mp3"   # change to your file name

# output folder for stems
output_dir = "demucs_output"

print("\n===== STARTING DEMUCS SEPARATION =====\n")

# Step 1: Separate stems
stem_paths = separate_polyphonic(audio_file, output_dir)

print("\n===== STEM PATHS =====")
for k, v in stem_paths.items():
    print(f"{k}: {v}")

# Step 2: Detect piano
print("\n===== RUNNING PIANO DETECTION =====\n")

is_piano = detect_piano_from_stems(stem_paths)

# Step 3: Final result
print("\n===== FINAL RESULT =====")

if is_piano:
    print("🎹 The song is detected as PIANO ONLY")
else:
    print("🎼 The song contains MULTIPLE INSTRUMENTS")