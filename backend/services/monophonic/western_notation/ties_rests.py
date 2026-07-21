# backend/services/monophonic/western_notation/ties_rests.py

"""
FIX (CRITICAL): The original code marked a tie "start" but never created
the continuation note in the next measure, producing unterminated ties in
MusicXML that renderers either ignore or misinterpret.

Correct approach:
- If a note overflows the current measure, SPLIT it at the barline.
- The first fragment gets tie="start", the second gets tie="stop".
- The second fragment is prepended to the next measure.
- After all splits, fill any remaining beat deficit with a rest.
"""


def _note_value_name(beats):
    """Return the closest standard duration name for a beat count."""
    NOTE_VALUES = {
        4.0:  "whole",
        3.0:  "dotted_half",
        2.0:  "half",
        1.5:  "dotted_quarter",
        1.0:  "quarter",
        0.75: "dotted_eighth",
        0.5:  "eighth",
        0.25: "sixteenth",
    }
    return min(NOTE_VALUES, key=lambda v: abs(v - beats))


def _split_note_at(note, split_beats, remaining_in_measure):
    """
    Split a note that overflows the current measure.

    Returns:
        first_part  — fits inside current measure (tie="start" if pitched)
        second_part — goes into the next measure   (tie="stop"  if pitched)
    """
    is_rest = note.get("note_name") in {None, "", "R", "REST", "Rest", "SILENCE"}

    first_beats  = remaining_in_measure
    second_beats = split_beats - remaining_in_measure

    first_beats  = round(first_beats,  4)
    second_beats = round(second_beats, 4)

    first = {
        **note,
        "quantized_beats": first_beats,
        "duration_beats":  first_beats,
        "duration_name":   _note_value_name(first_beats),
    }
    second = {
        **note,
        "quantized_beats": second_beats,
        "duration_beats":  second_beats,
        "duration_name":   _note_value_name(second_beats),
    }

    if not is_rest:
        first["tie"]  = "start"
        second["tie"] = "stop"
    else:
        # Rests are never tied — just split silently
        first.pop("tie",  None)
        second.pop("tie", None)

    return first, second


def apply_ties_and_rests(measures, beats_per_measure):
    """
    For each measure:
      1. Walk through notes; if a note overflows, split it and carry the
         remainder into the next measure via a carryover queue.
      2. After processing all notes, fill any beat deficit with a rest.

    Args:
        measures:          list of lists of note dicts (from measure_grouping)
        beats_per_measure: int or float, e.g. 4 for 4/4

    Returns:
        new_measures: list of corrected measure note lists
    """

    EPS = 1e-3  # floating-point tolerance

    new_measures = []
    carryover = []   # notes that overflowed from the previous measure

    for measure_notes in measures:

        current_measure = []
        current_beats   = 0.0

        # Process carried-over notes from previous measure first
        pending = carryover + list(measure_notes)
        carryover = []

        for note in pending:
            dur = float(note.get("quantized_beats", 0.0))

            if dur <= 0:
                continue  # skip zero-length junk

            remaining = beats_per_measure - current_beats

            if current_beats + dur <= beats_per_measure + EPS:
                # Note fits cleanly
                current_measure.append(note)
                current_beats += dur

            else:
                # Note overflows — split at the barline
                if remaining > EPS:
                    first, second = _split_note_at(note, dur, remaining)
                    current_measure.append(first)
                    current_beats += first["quantized_beats"]

                    # The second part carries into the next measure
                    # (it may itself be >1 measure long, handled next iteration)
                    carryover.append(second)
                else:
                    # No space at all in this measure — push entire note forward
                    carryover.append(note)

        # Fill remaining beats with a rest
        deficit = beats_per_measure - current_beats
        if deficit > EPS:
            current_measure.append({
                "pitch":           0,
                "quantized_beats": round(deficit, 4),
                "duration_beats":  round(deficit, 4),
                "duration_name":   _note_value_name(deficit),
                "note_name":       "Rest",
                "midi":            None,
            })

        new_measures.append(current_measure)

    # If carryover remains after all measures, append an extra measure
    # (happens when the last note was split but there's no next measure)
    while carryover:
        extra_measure = []
        extra_beats   = 0.0
        still_carry   = []

        for note in carryover:
            dur = float(note.get("quantized_beats", 0.0))
            if dur <= 0:
                continue
            remaining = beats_per_measure - extra_beats

            if extra_beats + dur <= beats_per_measure + EPS:
                extra_measure.append(note)
                extra_beats += dur
            else:
                first, second = _split_note_at(note, dur, remaining)
                extra_measure.append(first)
                extra_beats += first["quantized_beats"]
                still_carry.append(second)

        deficit = beats_per_measure - extra_beats
        if deficit > EPS:
            extra_measure.append({
                "pitch":           0,
                "quantized_beats": round(deficit, 4),
                "duration_beats":  round(deficit, 4),
                "duration_name":   _note_value_name(deficit),
                "note_name":       "Rest",
                "midi":            None,
            })

        new_measures.append(extra_measure)
        carryover = still_carry

    return new_measures