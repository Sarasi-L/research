import librosa
import numpy as np

def detect_piano_only(audio_path):

    y, sr = librosa.load(audio_path, sr=None)

    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

    rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))

    harmonic, percussive = librosa.effects.hpss(y)

    harmonic_energy = np.sum(harmonic**2)
    perc_energy = np.sum(percussive**2)

    ratio = harmonic_energy / (perc_energy + 1e-6)

    chroma = np.mean(librosa.feature.chroma_stft(y=y, sr=sr))

    if ratio > 5 and centroid < 2500 and rolloff < 4000 and chroma > 0.3:
        return True

    return False