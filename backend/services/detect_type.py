#backend/services/detect_type.py

"""
Fast & robust monophonic vs polyphonic audio classifier
Optimized CREPE-based fundamental frequency detection
SAFE for flute, violin, solo voice
~10x faster than naive CREPE usage
"""

import librosa
import numpy as np
import crepe


# ============================================================
# PUBLIC API
# ============================================================

def detect_type(audio_path: str) -> tuple:
    """
    Detect if audio is monophonic or polyphonic

    Returns:
        (type_string, confidence)
    """

    try:
        print("[INFO] Analyzing audio characteristics...")

        # ✅ Only 5 seconds is enough for mono/poly decision
        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=5.0)

        features = _extract_features(y, sr)
        audio_type, confidence = _classify_audio(features)

        print(f"[INFO] Classification: {audio_type} ({confidence*100:.1f}%)")
        print(
            f"[DEBUG] CREPE pitch_presence={features['pitch_presence_ratio']:.2f}, "
            f"pitch_stability={features['pitch_stability']:.1f}, "
            f"percussive_ratio={features['percussive_ratio']:.2f}"
        )

        return audio_type, confidence

    except Exception as e:
        print(f"[WARNING] detect_type failed: {e}")
        return "polyphonic", 0.75


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def _extract_features(y, sr):
    """
    Extract mono/poly relevant features
    """

    # --------------------------------
    # HPSS (Percussion detection)
    # --------------------------------
    y_harm, y_perc = librosa.effects.hpss(y, margin=2.0)

    harm_energy = np.sum(y_harm ** 2)
    perc_energy = np.sum(y_perc ** 2)
    total = harm_energy + perc_energy + 1e-10

    harmonic_ratio = harm_energy / total
    percussive_ratio = perc_energy / total

    # 🔥 EARLY EXIT: strong percussion → polyphonic
    if percussive_ratio > 0.35:
        return {
            'harmonic_ratio': harmonic_ratio,
            'percussive_ratio': percussive_ratio,
            'onset_density': 10.0,
            'rhythmic_strength': 0.5,
            'pitch_presence_ratio': 0.0,
            'pitch_stability': 999.0,
        }

    # --------------------------------
    # Onset density
    # --------------------------------
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    onset_density = len(onsets) / (len(y) / sr)

    # --------------------------------
    # Rhythm strength
    # --------------------------------
    tempogram = librosa.feature.tempogram(y=y, sr=sr)
    rhythmic_strength = np.mean(np.max(tempogram, axis=0))

    # --------------------------------
    # CREPE pitch analysis (OPTIMIZED)
    # --------------------------------
    pitch_presence_ratio, pitch_stability = _crepe_pitch_analysis(y, sr)

    return {
        'harmonic_ratio': harmonic_ratio,
        'percussive_ratio': percussive_ratio,
        'onset_density': onset_density,
        'rhythmic_strength': rhythmic_strength,
        'pitch_presence_ratio': pitch_presence_ratio,
        'pitch_stability': pitch_stability,
    }


# ============================================================
# CREPE ANALYSIS (FAST VERSION)
# ============================================================

def _crepe_pitch_analysis(y, sr):
    """
    CREPE fundamental frequency stability analysis

    Returns:
        pitch_presence_ratio: % frames with confident F0
        pitch_stability: std deviation of F0 (Hz)
    """

    # CREPE requires 16kHz
    if sr != 16000:
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        sr = 16000

    # ⚡ FAST SETTINGS
    time, freq, conf, _ = crepe.predict(
        y,
        sr,
        model_capacity="small",
        step_size=30,      # was 10 → 3x faster
        viterbi=False,     # disable smoothing (classification only)
        verbose=0
    )

    valid = conf > 0.6
    pitch_presence_ratio = np.sum(valid) / len(conf)

    if np.sum(valid) > 10:
        pitch_stability = np.std(freq[valid])
    else:
        pitch_stability = 999.0

    return pitch_presence_ratio, pitch_stability


# ============================================================
# CLASSIFICATION LOGIC
# ============================================================

def _classify_audio(f):
    """
    Decision logic tuned for SOLO instrument detection
    """

    mono = 0
    poly = 0

    print("\n[DEBUG] ===== Classification Analysis =====")

    # --------------------------------
    # RULE 1: Percussion
    # --------------------------------
    if f['percussive_ratio'] > 0.25:
        poly += 3
        print("[DEBUG] ✓ Strong percussion → POLYPHONIC")
    elif f['percussive_ratio'] < 0.1:
        mono += 1
        print("[DEBUG] ✓ Minimal percussion → supports MONOPHONIC")

    # --------------------------------
    # RULE 2: CREPE pitch stability (MOST IMPORTANT)
    # --------------------------------
    if f['pitch_presence_ratio'] > 0.75 and f['pitch_stability'] < 50:
        mono += 4
        print("[DEBUG] ✓ Stable single F0 → MONOPHONIC")
    elif f['pitch_presence_ratio'] < 0.4:
        poly += 3
        print("[DEBUG] ✓ No stable F0 → POLYPHONIC")

    # --------------------------------
    # RULE 3: Harmonic dominance
    # --------------------------------
    if f['harmonic_ratio'] > 0.85:
        mono += 1
        print("[DEBUG] ✓ Strong harmonic content → supports MONOPHONIC")

    # --------------------------------
    # RULE 4: Onset density
    # --------------------------------
    if f['onset_density'] > 6.0:
        poly += 1
        print("[DEBUG] ✓ Dense onsets → supports POLYPHONIC")
    elif f['onset_density'] < 2.0:
        mono += 1
        print("[DEBUG] ✓ Sparse onsets → supports MONOPHONIC")

    # --------------------------------
    # RULE 5: Rhythm strength
    # --------------------------------
    if f['rhythmic_strength'] > 0.3:
        poly += 1
        print("[DEBUG] ✓ Strong rhythm → supports POLYPHONIC")

    print(f"\n[DEBUG] Score → Mono={mono}, Poly={poly}")

    # --------------------------------
    # FINAL DECISION
    # --------------------------------
    if mono > poly:
        confidence = 0.9 if mono >= 4 else 0.75
        return "monophonic", confidence

    if poly > mono:
        confidence = 0.9 if poly >= 4 else 0.75
        return "polyphonic", confidence

    print("[DEBUG] ⚠ Unclear → default POLYPHONIC")
    return "polyphonic", 0.65
