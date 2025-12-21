# backend/services/monophonic/validation/validate_notes.py

from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes

def validate_note_segmentation(y, sr):
    """
    Validate note segmentation from preprocessed audio.
    y: waveform
    sr: sample rate
    """
    time, freq, conf = extract_pitch(y, sr)
    notes = frames_to_notes(time, freq, conf)

    print("\n[VALIDATION] NOTE EVENTS")
    print(f"Total notes detected: {len(notes)}\n")

    for n in notes[:10]:  # show first 10 notes
        print(n)

    avg_duration = sum(n["end"] - n["start"] for n in notes) / len(notes)

    return {
        "note_count": len(notes),
        "avg_note_duration_sec": round(avg_duration, 3),
        "first_note": notes[0] if notes else None
    }
