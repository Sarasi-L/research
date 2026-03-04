from music21 import converter
import numpy as np


def score_integrity_validation(midi_path: str):
    print("\n[VALIDATION] ===== Score Integrity Validation =====")

    score = converter.parse(midi_path)

    errors = {
        "overlapping_notes": 0,
        "extreme_durations": 0,
        "high_polyphony": 0
    }

    for part in score.parts:
        notes = list(part.recurse().notes)

        for i in range(len(notes) - 1):
            n1 = notes[i]
            n2 = notes[i + 1]

            # Overlap check
            if n1.offset + n1.quarterLength > n2.offset:
                errors["overlapping_notes"] += 1

            # Impossible durations
            if n1.quarterLength > 8 or n1.quarterLength < 0.0625:
                errors["extreme_durations"] += 1

        # Polyphony check
        simult = {}
        for n in notes:
            simult.setdefault(n.offset, 0)
            simult[n.offset] += 1

        max_poly = max(simult.values()) if simult else 0
        if max_poly > 10:
            errors["high_polyphony"] += 1

    print("\n=== Score Integrity Report ===")
    for k, v in errors.items():
        print(f"{k}: {v}")

    return errors