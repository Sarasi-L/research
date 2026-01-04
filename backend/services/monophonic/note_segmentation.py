# backend/services/monophonic/note_segmentation.py

import numpy as np

# -------------------------------------------------
# Instrument pitch ranges (Hz)
# -------------------------------------------------
INSTRUMENT_PITCH_RANGES = {
    "flute":  (260, 2100),
    "violin": (196, 3500),
    "voice":  (80, 1100),
    "cello":  (65, 660),
    "organ":  (16, 3500)
}


# -------------------------------------------------
# Frame → Note segmentation
# -------------------------------------------------
def frames_to_notes(
    time,
    freq,
    conf,
    instrument=None,
    conf_thresh=0.6,
    pitch_change_thresh=50.0,
    min_note_duration=0.08
):
    """
    Convert CREPE pitch frames to raw musical note events

    Returns:
    [
      { "start": float, "end": float, "pitch": float }
    ]
    """

    # Instrument-aware pitch limits
    min_pitch, max_pitch = (0, float("inf"))
    if instrument and instrument in INSTRUMENT_PITCH_RANGES:
        min_pitch, max_pitch = INSTRUMENT_PITCH_RANGES[instrument]

    notes = []
    current_start = None
    current_pitch = None

    for i in range(len(freq)):

        # Frame is voiced & valid
        voiced = conf[i] >= conf_thresh and not np.isnan(freq[i])
        if voiced and not (min_pitch <= freq[i] <= max_pitch):
            voiced = False

        # ---------------- End note ----------------
        if not voiced:
            if current_start is not None:
                end_time = time[i]
                if end_time - current_start >= min_note_duration:
                    notes.append({
                        "start": round(current_start, 3),
                        "end": round(end_time, 3),
                        "pitch": round(current_pitch, 2)
                    })
                current_start = None
                current_pitch = None
            continue

        # ---------------- Start note ----------------
        if current_start is None:
            current_start = time[i]
            current_pitch = freq[i]
            continue

        # ---------------- Pitch change → new note ----------------
        if abs(freq[i] - current_pitch) > pitch_change_thresh:
            end_time = time[i]
            if end_time - current_start >= min_note_duration:
                notes.append({
                    "start": round(current_start, 3),
                    "end": round(end_time, 3),
                    "pitch": round(current_pitch, 2)
                })
            current_start = time[i]
            current_pitch = freq[i]

        else:
            # Smooth pitch tracking
            current_pitch = 0.9 * current_pitch + 0.1 * freq[i]

    # Close final note
    if current_start is not None:
        notes.append({
            "start": round(current_start, 3),
            "end": round(time[-1], 3),
            "pitch": round(current_pitch, 2)
        })

    return notes


# -------------------------------------------------
# NOTE DURATION SMOOTHING  (CRITICAL FIX)
# -------------------------------------------------
def smooth_note_durations(notes, min_duration=0.15):
    """
    Merge extremely short notes into neighboring notes
    to prevent micro-segmentation from CREPE.

    This MUST be applied before tempo estimation
    and quantization.
    """

    if not notes:
        return notes

    smoothed = []
    current = notes[0].copy()

    for n in notes[1:]:
        current_dur = current["end"] - current["start"]

        # If current note is too short → merge
        if current_dur < min_duration:
            current["end"] = n["end"]
            current["pitch"] = (
                0.7 * current["pitch"] + 0.3 * n["pitch"]
            )
        else:
            smoothed.append(current)
            current = n.copy()

    smoothed.append(current)
    return smoothed
