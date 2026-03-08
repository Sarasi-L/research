import librosa
import numpy as np


def detect_piano_from_stems(stem_paths, threshold=0.02):
    """
    Decide if audio is piano-only using Demucs stems.

    Parameters
    ----------
    stem_paths : dict
        {"vocals": path, "drums": path, "bass": path, "other": path}

    Returns
    -------
    bool
        True  → piano-only
        False → multi-instrument
    """

    energies = {}

    for name, path in stem_paths.items():
        y, sr = librosa.load(path, sr=None)

        # normalize energy by length
        energy = np.sum(y ** 2) / len(y)
        energies[name] = energy

    print("\n[STEM ENERGY]")
    for k, v in energies.items():
        print(f"{k}: {v:.6f}")

    vocals = energies.get("vocals", 0)
    drums = energies.get("drums", 0)
    bass = energies.get("bass", 0)

    # if these stems are almost silent → likely piano
    if vocals < threshold and drums < threshold and bass < threshold:
        print("\nDetected: PIANO ONLY")
        return True

    print("\nDetected: MULTI-INSTRUMENT")
    return False