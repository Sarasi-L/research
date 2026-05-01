# backend/services/polyphonic/transcribe_audio.py

import numpy as np
import pretty_midi
from pathlib import Path

from services.polyphonic.multipitch_detection import detect_multipitch


def transcribe_with_onsets_frames(audio_path: str, output_dir: Path):
    """
    Primary transcription using Onsets & Frames (via detect_multipitch)
    Falls back to Basic Pitch if detection fails
    """

    print("\n[TRANSCRIBE] Using Onsets & Frames...")

    notes = detect_multipitch(audio_path, post_process=True)

    # Fallback check
    if not notes or len(notes) < 10:
        print("[TRANSCRIBE] Too few notes detected, falling back to Basic Pitch")

        from backend.services.polyphonic.transcribe_basic_pitch import transcribe_stem

        midi_path = transcribe_stem(audio_path, str(output_dir))
        return midi_path

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    for n in notes:

        velocity = int(np.clip(n["velocity"] * 127, 30, 110))

        note = pretty_midi.Note(
            velocity=velocity,
            pitch=n["pitch"],
            start=n["onset"],
            end=n["offset"],
        )

        instrument.notes.append(note)

    midi.instruments.append(instrument)

    midi_path = output_dir / "transcribed.mid"
    midi.write(str(midi_path))

    print(f"[TRANSCRIBE] MIDI created: {midi_path}")

    return str(midi_path)