import os
from backend.services.polyphonic.voice_separation import separate_voices
from backend.services.polyphonic.multipitch_detection import detect_multipitch

# ------------------------------
# Example uploaded polyphonic audio
# ------------------------------
audio_file = "mix7 poly.mp3"

print("\n[PIPELINE] ===== Starting Polyphonic Pipeline =====")

# ------------------------------
# Step 1: Voice Separation
# ------------------------------
voices = separate_voices(audio_file)
print(f"[PIPELINE] Total voices separated: {len(voices)}\n")

# ------------------------------
# Step 2: Multipitch Detection for each voice
# ------------------------------
all_notes = []

for v in voices:
    print(f"[PIPELINE] ===== Processing voice: {v['voice_name']} =====")
    
    # Run multipitch detection on separated voice
    notes = detect_multipitch(v["file_path"])
    all_notes.extend(notes)
    
    print(f"[PIPELINE] Notes detected in {v['voice_name']}: {len(notes)}\n")

# ------------------------------
# Step 3: Final summary
# ------------------------------
print("\n[PIPELINE] ===== Full Pipeline Completed =====")
print(f"[PIPELINE] Total voices processed: {len(voices)}")
print(f"[PIPELINE] Total notes detected across all voices: {len(all_notes)}")

if all_notes:
    pitches = [n["pitch"] for n in all_notes]
    print(f"[PIPELINE] Overall pitch range: {min(pitches)} → {max(pitches)}")
    print(f"[PIPELINE] First note detected: {all_notes[0]}")

# ------------------------------
# Optional: Clean up temporary separated voice files
# ------------------------------
for v in voices:
    if "voice_" not in audio_file:  # do not delete original
        try:
            os.remove(v["file_path"])
        except Exception:
            pass
