from pathlib import Path
from backend.services.preprocess import preprocess_audio
from backend.services.detect_type import detect_audio_type
from backend.services.separate_demucs import separate_polyphonic

BASE = Path("backend/temp")
UPLOADS = BASE / "uploads"
STEMS = BASE / "stems"

UPLOADS.mkdir(parents=True, exist_ok=True)
STEMS.mkdir(parents=True, exist_ok=True)

# 1. Input file
input_file = Path("test_audio/mix1.mp3")

# 2. Preprocess audio
processed_file = UPLOADS / "song_processed.wav"
preprocess_audio(str(input_file), str(processed_file))
print(f"[INFO] Preprocessed audio saved at: {processed_file}")

# 3. Detect type
audio_type, confidence = detect_audio_type(str(processed_file))
print(f"[INFO] Audio type: {audio_type}, Confidence: {confidence:.2f}")

# 4. If polyphonic, separate stems
if audio_type == "polyphonic":
    output_dir = STEMS / "test_stems"
    stem_paths = separate_polyphonic(str(processed_file), output_dir)
    print(f"[INFO] Stems saved at: {output_dir}")
    for name, path in stem_paths.items():
        print(f"  {name}: {path}")
else:
    print("[INFO] Audio is monophonic, no stems separated.")
