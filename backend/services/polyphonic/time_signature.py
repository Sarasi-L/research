# backend/services/polyphonic/time_signature.py

import librosa
import numpy as np

def detect_time_signature(audio_path: str, beat_times):
    """
    Estimate time signature: 3/4, 4/4, or 6/8.
    Based on beat intervals + onset patterns.
    """
    print("\n[TIME] ===== Detecting Time Signature =====")

    # beat intervals in seconds
    intervals = np.diff(beat_times)

    if len(intervals) < 4:
        print("[TIME] Not enough beats → default 4/4")
        return 4, 4

    avg_interval = np.mean(intervals)

    # Load onset envelope
    y, sr = librosa.load(audio_path, mono=True)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env)

    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # Count onsets between beats
    onsets_per_beat = []
    for i in range(len(beat_times) - 1):
        start = beat_times[i]
        end = beat_times[i + 1]
        count = np.sum((onset_times >= start) & (onset_times < end))
        onsets_per_beat.append(count)

    mean_onsets = np.mean(onsets_per_beat)

    # Rules
    # Most modern songs are 4/4
    if mean_onsets > 3.2:
        print("[TIME] Time signature: 6/8")
        return 6, 8

    elif 2.0 < mean_onsets <= 3.2:
        print("[TIME] Time signature: 3/4")
        return 3, 4

    else:
        print("[TIME] Time signature: 4/4 (default)")
        return 4, 4