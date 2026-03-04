# backend/services/polyphonic/beat_tracking.py

import librosa
import numpy as np

def detect_beats(audio_path: str):
    """
    Detect tempo + beat grid positions using librosa.
    Returns:
        tempo (float)
        beat_times (numpy array)
    """
    print("\n[BEAT] ===== Tempo + Beat Tracking =====")
    print(f"[BEAT] Loading audio: {audio_path}")

    y, sr = librosa.load(audio_path, mono=True)

    print("[BEAT] Detecting tempo...")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # 🔧 FIX: Ensure tempo is float
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])

    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    print(f"[BEAT] Tempo detected: {tempo:.2f} BPM")
    print(f"[BEAT] Beats detected: {len(beat_times)}")

    return tempo, beat_times