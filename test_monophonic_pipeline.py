from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.pitch_extraction import extract_pitch

AUDIO_PATH = "mix7.mp3"
INSTRUMENT = "flute"

# STEP 3
y, sr = preprocess_audio(AUDIO_PATH, INSTRUMENT)
print("[OK] Preprocessing completed")

# STEP 4
t, f0, conf = extract_pitch(y, sr)
print("[OK] Pitch extraction completed")

print(f"Frames: {len(f0)}")
print(f"Voiced frames: {(~(f0 != f0)).sum()}")
