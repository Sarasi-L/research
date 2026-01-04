import librosa
import numpy as np
from pathlib import Path

from backend.services.detect_type_crepe import detect_type
from backend.services.detect_instruments import detect_all_instruments
from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes
from backend.services.monophonic.musicxml_utils import create_musicxml


def process_audio_file(audio_path, part_name="Flute"):
    print(f"\n🎵 Processing audio: {audio_path}")

    # 1️⃣ Load audio (FORCE MONO)
    y, sr = librosa.load(audio_path, sr=16000, mono=True)

    # Normalize (VERY IMPORTANT)
    if np.max(np.abs(y)) > 0:
        y = y / np.max(np.abs(y))

    print(f"[INFO] Audio loaded | sr={sr}, duration={len(y)/sr:.2f}s")

    # 2️⃣ Mono / Poly detection
    audio_type, confidence = detect_type(y, sr)
    print(f"[INFO] Type: {audio_type} ({confidence})")

    if audio_type != "monophonic":
        raise ValueError("This test script supports monophonic audio only")

    # 3️⃣ Instrument detection (YAMNet)
    instruments = detect_all_instruments(audio_path)
    print(f"[INFO] Detected instruments: {instruments}")

    # 4️⃣ Pitch extraction (CREPE)
    print("[INFO] Extracting pitch...")
    times, f0, conf = extract_pitch(
        y,
        sr,
        confidence_threshold=0.2   # 🔥 LOWERED
    )

    valid = ~np.isnan(f0)
    print(f"[DEBUG] Valid pitch frames: {np.sum(valid)}/{len(f0)}")

    if np.sum(valid) == 0:
        raise RuntimeError("❌ No pitch points extracted")

    # 5️⃣ Frames → Notes
    notes = frames_to_notes(times, f0, conf)

    if len(notes) == 0:
        raise RuntimeError("❌ No notes formed")

    print(f"[INFO] Extracted {len(notes)} notes")

    # 6️⃣ Create MusicXML
    output_path = Path("output_flute.xml")

    create_musicxml(
        notes=notes,
        output_path=output_path,
        part_name=part_name,
        key="C",          # default
        time_signature="4/4",
        tempo=120
    )

    print(f"✅ MusicXML generated: {output_path.resolve()}")


if __name__ == "__main__":
    process_audio_file("mix7.mp3")
