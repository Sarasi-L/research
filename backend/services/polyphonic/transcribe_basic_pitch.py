# backend/services/polyphonic/transcribe_basic_pitch.py

from pathlib import Path
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
import pretty_midi
import numpy as np


MIN_NOTE_DURATION = 0.04  
MERGE_THRESHOLD = 0.05    


def clean_notes(note_events):
    

    cleaned = []

    
    note_events = sorted(note_events, key=lambda x: x[0])

    for note in note_events:

        # Handle different BasicPitch output formats
        if len(note) == 4:
            start, end, pitch, amplitude = note
        elif len(note) >= 5:
            start, end, pitch, amplitude = note[:4]
        else:
            continue

        duration = end - start

        # Remove short noisy notes
        if duration < MIN_NOTE_DURATION:
            continue

        velocity = int(np.clip(amplitude * 127, 30, 110))

        cleaned.append({
            "start": float(start),
            "end": float(end),
            "pitch": int(pitch),
            "velocity": velocity
        })

    # Merge duplicate notes
    merged = []
    for note in cleaned:
        if not merged:
            merged.append(note)
            continue

        last = merged[-1]

        same_pitch = note["pitch"] == last["pitch"]
        small_gap = abs(note["start"] - last["end"]) < MERGE_THRESHOLD

        if same_pitch and small_gap:
            last["end"] = note["end"]
            last["velocity"] = int((last["velocity"] + note["velocity"]) / 2)
        else:
            merged.append(note)

    # Velocity smoothing
    for i in range(1, len(merged)):
        diff = merged[i]["velocity"] - merged[i - 1]["velocity"]
        if abs(diff) > 40:
            merged[i]["velocity"] = int(
                merged[i - 1]["velocity"] + (diff * 0.5)
            )

    return merged


def build_clean_midi(cleaned_notes):
   

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    for note in cleaned_notes:
        midi_note = pretty_midi.Note(
            velocity=int(note["velocity"]),
            pitch=note["pitch"],
            start=float(note["start"]),
            end=float(note["end"])
        )
        instrument.notes.append(midi_note)

    midi.instruments.append(instrument)

    return midi


def transcribe_stem(audio_path: str, output_dir: str):
  

    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[BP] ===== Transcribing: {audio_path.name} =====")

    midi_output_path = output_dir / f"{audio_path.stem}.mid"

    print("[BP] Running Basic Pitch model...")

    model_output, midi_data, note_events = predict(
        str(audio_path),
        model_or_model_path=ICASSP_2022_MODEL_PATH,
    )

    print(f"[BP] Raw detected notes: {len(note_events)}")

    # Apply post-processing
    cleaned_notes = clean_notes(note_events)

    print(f"[BP] Cleaned notes count: {len(cleaned_notes)}")

    # Build cleaned MIDI
    cleaned_midi = build_clean_midi(cleaned_notes)

    cleaned_midi.write(str(midi_output_path))

    print(f"[BP] ✓ Cleaned MIDI saved to: {midi_output_path}")

    return str(midi_output_path)