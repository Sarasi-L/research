# backend/app.py
import os
from pathlib import Path
from preprocess import preprocess_audio
from instrument_separate import separate_instruments
from preprocess_separated import generate_spectrogram

try:
    # ===== Paths =====
    input_file = Path("audio_input/mixed_song.wav")
    preprocessed_file = Path("preprocessed/mixed_song.wav")
    separated_dir = Path("separated")
    spectrogram_dir = Path("preprocessed/spectrograms")
    spectrogram_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Step 1: Preprocessing Mixed Audio")
    preprocess_audio(str(input_file), str(preprocessed_file))

    print("[INFO] Step 2: Instrument Separation")
    separate_instruments(str(preprocessed_file), str(separated_dir))

    print("[INFO] Step 3: Generate Spectrograms for Each Instrument")
    for instrument_file in separated_dir.glob("*.wav"):
        out_file = spectrogram_dir / f"{instrument_file.stem}.png"
        generate_spectrogram(str(instrument_file), str(out_file))

    print("[SUCCESS] All steps completed successfully!")

except Exception as e:
    print(f"[ERROR] Pipeline failed: {e}")
