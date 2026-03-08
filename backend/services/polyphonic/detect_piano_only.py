import librosa
import numpy as np

def detect_piano_only(audio_path):

    y, sr = librosa.load(audio_path, sr=None)

    # spectral centroid
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

    # harmonic ratio
    harmonic, percussive = librosa.effects.hpss(y)

    harmonic_energy = np.sum(harmonic**2)
    perc_energy = np.sum(percussive**2)

    ratio = harmonic_energy / (perc_energy + 1e-6)

    # piano heuristic
    if ratio > 4 and centroid < 3000:
        return True

    return False