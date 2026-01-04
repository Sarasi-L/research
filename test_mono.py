import librosa
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
AUDIO_PATH = "mono2.wav"   # <-- change this
SR = 16000

# Pitch range (generic melodic instrument)
FMIN = 80
FMAX = 2000

# =========================
# LOAD AUDIO
# =========================
y, sr = librosa.load(AUDIO_PATH, sr=SR, mono=True)
duration = len(y) / sr

print("Sample rate:", sr)
print("Duration (sec):", round(duration, 2))

# =========================
# PITCH EXTRACTION (YIN)
# =========================
f0 = librosa.yin(
    y,
    fmin=FMIN,
    fmax=FMAX,
    sr=sr,
    frame_length=2048,
    hop_length=512
)

total_frames = len(f0)
voiced_frames = np.sum(~np.isnan(f0))

print("\n===== BASIC STATS =====")
print("Total frames :", total_frames)
print("Voiced frames:", voiced_frames)
print("Voiced ratio :", round(voiced_frames / total_frames, 2))

print("\nFirst 40 raw pitch values (Hz):")
print(f0[:40])

# =========================
# OCTAVE ERROR CORRECTION
# =========================
def remove_octave_errors(f0):
    f0_clean = f0.copy()

    for i in range(1, len(f0_clean)):
        if np.isnan(f0_clean[i]) or np.isnan(f0_clean[i-1]):
            continue

        ratio = f0_clean[i] / f0_clean[i-1]

        # Downward octave
        if ratio > 1.9:
            f0_clean[i] /= 2

        # Upward octave
        elif ratio < 0.55:
            f0_clean[i] *= 2

    return f0_clean

f0_corrected = remove_octave_errors(f0)

print("\nFirst 40 corrected pitch values (Hz):")
print(f0_corrected[:40])

# =========================
# MONOPHONIC ANALYSIS
# =========================
valid_f0 = f0_corrected[~np.isnan(f0_corrected)]

pitch_mean = np.mean(valid_f0)
pitch_std = np.std(valid_f0)
silence_ratio = np.sum(np.isnan(f0_corrected)) / total_frames

print("\n===== PITCH ANALYSIS =====")
print("Pitch mean (Hz):", round(pitch_mean, 2))
print("Pitch std  (Hz):", round(pitch_std, 2))
print("Silence ratio :", round(silence_ratio, 2))

# =========================
# FINAL DECISION (ROBUST)
# =========================
is_monophonic = (
    pitch_std < 25 and       # stable pitch after octave fix
    voiced_frames > 10 and   # enough voiced frames
    silence_ratio < 0.5
)

print("\n===== FINAL RESULT =====")
if is_monophonic:
    print("✅ AUDIO IS MONOPHONIC")
else:
    print("❌ AUDIO IS NOT MONOPHONIC / UNSTABLE")

# =========================
# VISUALIZATION
# =========================
plt.figure(figsize=(12, 4))
plt.plot(f0, label="Raw f0", alpha=0.4)
plt.plot(f0_corrected, label="Corrected f0", linewidth=2)
plt.legend()
plt.title("Pitch Contour (Before vs After Octave Correction)")
plt.xlabel("Frame")
plt.ylabel("Frequency (Hz)")
plt.grid(True)
plt.tight_layout()
plt.show()
