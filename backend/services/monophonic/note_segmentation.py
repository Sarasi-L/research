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
    Convert CREPE pitch frames to raw musical note events.

    FIX: Instead of exponential smoothing (which drifts pitch over time),
    we now collect all frames belonging to a note and take the median
    at note-end. This gives a stable, accurate pitch per note.

    Returns:
    [
      { "start": float, "end": float, "pitch": float }
    ]
    """

    min_pitch, max_pitch = (0, float("inf"))
    if instrument and instrument in INSTRUMENT_PITCH_RANGES:
        min_pitch, max_pitch = INSTRUMENT_PITCH_RANGES[instrument]

    notes = []
    current_start = None
    current_frames = []   # FIX: collect frames instead of running average

    for i in range(len(freq)):

        # Frame is voiced & valid
        voiced = (
            conf[i] >= conf_thresh
            and freq[i] is not None
            and not np.isnan(freq[i])
        )
        if voiced and not (min_pitch <= freq[i] <= max_pitch):
            voiced = False

        # ---------------- End note ----------------
        if not voiced:
            if current_start is not None and len(current_frames) > 0:
                end_time = time[i]
                if end_time - current_start >= min_note_duration:
                    # FIX: median of all frames → accurate, outlier-resistant pitch
                    stable_pitch = float(np.median(current_frames))
                    notes.append({
                        "start": round(current_start, 3),
                        "end": round(end_time, 3),
                        "pitch": round(stable_pitch, 2)
                    })
                current_start = None
                current_frames = []
            continue

        # ---------------- Start note ----------------
        if current_start is None:
            current_start = time[i]
            current_frames = [freq[i]]
            continue

        # ---------------- Pitch change → new note ----------------
        # FIX: compare against median of current note, not drifted running avg
        current_median = float(np.median(current_frames))
        if abs(freq[i] - current_median) > pitch_change_thresh:
            end_time = time[i]
            if end_time - current_start >= min_note_duration:
                stable_pitch = float(np.median(current_frames))
                notes.append({
                    "start": round(current_start, 3),
                    "end": round(end_time, 3),
                    "pitch": round(stable_pitch, 2)
                })
            current_start = time[i]
            current_frames = [freq[i]]
        else:
            current_frames.append(freq[i])

    # Close final note
    if current_start is not None and len(current_frames) > 0:
        stable_pitch = float(np.median(current_frames))
        notes.append({
            "start": round(current_start, 3),
            "end": round(time[-1], 3),
            "pitch": round(stable_pitch, 2)
        })

    return notes


# -------------------------------------------------
# NOTE DURATION SMOOTHING
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

        if current_dur < min_duration:
            # Extend end time and use pitch of the longer note
            current["end"] = n["end"]
            # FIX: don't blend pitches — keep the dominant (longer) note's pitch
            # The merged note inherits the next note's pitch since
            # the current one was too short to be reliable
            current["pitch"] = n["pitch"]
        else:
            smoothed.append(current)
            current = n.copy()

    smoothed.append(current)
    return smoothed