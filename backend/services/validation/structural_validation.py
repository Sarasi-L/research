from music21 import converter, note, chord
import numpy as np


def structural_validation(midi_path: str):
    print("\n[VALIDATION] ===== Structural Validation =====")

    try:
        score = converter.parse(midi_path)
    except Exception as e:
        print(f"❌ Error loading MIDI: {e}")
        return None

    report = {}

    # ------------------------------------------------
    # 1. Pitch & Duration Statistics
    # ------------------------------------------------
    pitches = []
    durations = []

    for element in score.recurse().notesAndRests:

        # Handle single notes
        if isinstance(element, note.Note):
            pitches.append(element.pitch.midi)
            durations.append(float(element.quarterLength))

        # Handle chords (including PercussionChord)
        elif isinstance(element, chord.Chord):
            for p in element.pitches:
                pitches.append(p.midi)
                durations.append(float(element.quarterLength))

        # Ignore rests automatically

    if not pitches:
        print("❌ No pitched notes found in MIDI.")
        return None

    report["total_notes"] = len(pitches)
    report["pitch_min"] = int(min(pitches))
    report["pitch_max"] = int(max(pitches))
    report["avg_pitch"] = round(float(np.mean(pitches)), 2)
    report["avg_duration"] = round(float(np.mean(durations)), 3)

    # ------------------------------------------------
    # 2. Tempo Detection
    # ------------------------------------------------
    try:
        tempos = score.metronomeMarkBoundaries()
        if tempos and tempos[0][2] is not None:
            report["tempo_bpm"] = tempos[0][2].number
        else:
            report["tempo_bpm"] = "Not detected"
    except Exception:
        report["tempo_bpm"] = "Not detected"

    # ------------------------------------------------
    # 3. Time Signature Detection
    # ------------------------------------------------
    try:
        ts = score.recurse().getElementsByClass("TimeSignature")
        if ts:
            report["time_signature"] = str(ts[0].ratioString)
        else:
            report["time_signature"] = "Not found"
    except Exception:
        report["time_signature"] = "Not found"

    # ------------------------------------------------
    # 4. Key Detection
    # ------------------------------------------------
    try:
        detected_key = score.analyze("key")
        report["detected_key"] = str(detected_key)
    except Exception:
        report["detected_key"] = "Analysis failed"

    # ------------------------------------------------
    # 5. Chord Consistency Analysis
    # ------------------------------------------------
    try:
        chordified = score.chordify()
        chords = list(chordified.recurse().getElementsByClass(chord.Chord))

        unique_chords = set()

        for c in chords:
            if c.pitches:
                unique_chords.add(tuple(p.midi for p in c.pitches))

        report["unique_chords"] = len(unique_chords)
        report["total_chords"] = len(chords)

    except Exception:
        report["unique_chords"] = 0
        report["total_chords"] = 0

    # ------------------------------------------------
    # Print Report
    # ------------------------------------------------
    print("\n=== Structural Report ===")
    for k, v in report.items():
        print(f"{k}: {v}")

    return report


# ------------------------------------------------
# Run directly (for testing)
# ------------------------------------------------
if __name__ == "__main__":
    structural_validation("backend/midi_output/full_song_key_ts.mid")