# backend/services/polyphonic/transcribe_drums.py

from pathlib import Path
import librosa
import pretty_midi
import numpy as np

def transcribe_drums(audio_path: str, output_dir: str):
    """
    Simple drum transcription using onset detection.
    Creates MIDI percussion track.
    """

    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[DRUM] ===== Transcribing: {audio_path.name} =====")

    # Load audio (mono)
    y, sr = librosa.load(audio_path, mono=True)

    print("[DRUM] Detecting onsets...")
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    print(f"[DRUM] Detected {len(onset_times)} drum hits")

    # Create MIDI object
    midi = pretty_midi.PrettyMIDI()

    # Channel 9 = percussion (MIDI standard)
    drum_instrument = pretty_midi.Instrument(
        program=0,
        is_drum=True
    )

    # Map all hits to snare (you can improve later)
    for onset in onset_times:
        note = pretty_midi.Note(
            velocity=100,
            pitch=38,  # 38 = Acoustic Snare
            start=float(onset),
            end=float(onset + 0.1)
        )
        drum_instrument.notes.append(note)

    midi.instruments.append(drum_instrument)

    midi_output_path = output_dir / "drums.mid"
    midi.write(str(midi_output_path))

    print(f"[DRUM] ✓ Drum MIDI saved to: {midi_output_path}")

    return str(midi_output_path)
