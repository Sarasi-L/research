#backend/services/monophonic/tempo_beat_estimation.py

import librosa
import numpy as np

def estimate_tempo_and_beats(audio_path):
    """
    Estimate tempo and beats from audio using Librosa
    """

    y, sr = librosa.load(audio_path, sr=None, mono=True)

    # Onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # Tempo (librosa returns array sometimes)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)

    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])

    # Beat tracking
    beats = librosa.beat.beat_track(
        onset_envelope=onset_env,
        sr=sr,
        units="time"
    )[1]

    beat_intervals = np.diff(beats) if len(beats) > 1 else np.array([])

    return {
        "tempo": round(float(tempo), 2),
        "beats": beats.tolist(),
        "beat_count": int(len(beats)),
        "mean_beat_interval": float(np.mean(beat_intervals)) if len(beat_intervals) else None,
        "beat_interval_std": float(np.std(beat_intervals)) if len(beat_intervals) else None
    }
