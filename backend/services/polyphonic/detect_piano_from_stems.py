# backend/services/polyphonic/detect_piano_from_stems.py

import librosa
import numpy as np


def detect_piano_from_stems(stem_paths):
    """
    Detect if the song is piano-only using Demucs stems.

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

    # ----------------------------------
    # Calculate raw energy of each stem
    # ----------------------------------
    for name, path in stem_paths.items():

        y, sr = librosa.load(path, sr=None)

        # energy of signal
        energy = np.sum(y ** 2)

        energies[name] = energy

    # ----------------------------------
    # Convert to ratios
    # ----------------------------------
    total_energy = sum(energies.values())

    ratios = {}

    for k, v in energies.items():
        ratios[k] = v / total_energy if total_energy > 0 else 0

    # ----------------------------------
    # Print debug info
    # ----------------------------------
    print("\n[STEM ENERGY RATIOS]")
    for k, v in ratios.items():
        print(f"{k}: {v:.3f}")

    drums_ratio = ratios.get("drums", 0)
    bass_ratio = ratios.get("bass", 0)
    vocals_ratio = ratios.get("vocals", 0)
    other_ratio = ratios.get("other", 0)

    # ----------------------------------
    # Decision logic
    # ----------------------------------

    # Strong drums or vocals → definitely multi instrument
    if drums_ratio > 0.08 or vocals_ratio > 0.08:
        print("\nDetected: MULTI-INSTRUMENT (drums or vocals present)")
        return False

    # If almost all energy is in "other" stem → likely piano
    if other_ratio > 0.80 and bass_ratio < 0.10:
        print("\nDetected: PIANO ONLY")
        return True

    print("\nDetected: MULTI-INSTRUMENT")
    return False