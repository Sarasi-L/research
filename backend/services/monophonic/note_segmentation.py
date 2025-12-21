# backend/services/monophonic/note_segmentation.py

import numpy as np

# Define pitch ranges for instruments
INSTRUMENT_PITCH_RANGES = {
    "flute":  (260, 2100),
    "violin": (196, 3500),
    "voice":  (80, 1100),
    "cello":  (65, 660),
    "organ":  (16, 3500)
}


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
    Convert pitch frames to musical note events

    Returns:
    [
      { "start": float, "end": float, "pitch": float }
    ]
    """

    # Set instrument pitch range
    min_pitch, max_pitch = (0, float("inf"))
    if instrument and instrument in INSTRUMENT_PITCH_RANGES:
        min_pitch, max_pitch = INSTRUMENT_PITCH_RANGES[instrument]

    notes = []
    current_start = None
    current_pitch = None

    for i in range(len(freq)):

        # Determine if frame is voiced and within instrument range
        voiced = conf[i] >= conf_thresh and not np.isnan(freq[i])
        if voiced and not (min_pitch <= freq[i] <= max_pitch):
            voiced = False  # Instrument-aware filtering

        if not voiced:
            # End current note
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

        # First voiced frame
        if current_start is None:
            current_start = time[i]
            current_pitch = freq[i]
            continue

        # Pitch jump → new note
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
            # Smooth pitch update
            current_pitch = 0.9 * current_pitch + 0.1 * freq[i]

    # Close last note
    if current_start is not None:
        notes.append({
            "start": round(current_start, 3),
            "end": round(time[-1], 3),
            "pitch": round(current_pitch, 2)
        })

    return notes
