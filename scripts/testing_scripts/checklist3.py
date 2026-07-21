import librosa
import numpy as np
import matplotlib.pyplot as plt
import crepe

# Paths (one sample each)
mono_path = "nsynth_00659.wav"
poly_path = "blues.00002.wav"

def extract_pitch(audio_path):
    """
    Extract pitch using CREPE with confidence scores
    Returns: time, frequency, confidence
    """
    y, sr = librosa.load(audio_path, sr=16000)
    y = y[:sr * 10]  # limit to 10 seconds

    time, frequency, confidence, _ = crepe.predict(
        y,
        sr,
        viterbi=True,
        step_size=10,
        model_capacity="medium"
    )

    # Store original frequency before masking for confidence display
    original_frequency = frequency.copy()
    
    # Mask low confidence frequencies
    frequency[confidence < 0.8] = np.nan
    
    return time, frequency, original_frequency, confidence

# Extract pitch and confidence for both files
t_mono, f_mono_filtered, f_mono_original, confidence_mono = extract_pitch(mono_path)
t_poly, f_poly_filtered, f_poly_original, confidence_poly = extract_pitch(poly_path)

# Create a more informative visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Load audio for spectrograms
y_mono, sr_mono = librosa.load(mono_path, sr=16000)
y_poly, sr_poly = librosa.load(poly_path, sr=16000)
y_mono = y_mono[:sr_mono * 5]  # First 5 seconds
y_poly = y_poly[:sr_poly * 5]   # First 5 seconds

# 1. Spectrogram comparison
ax = axes[0, 0]
D_mono = librosa.amplitude_to_db(np.abs(librosa.stft(y_mono)), ref=np.max)
librosa.display.specshow(D_mono, sr=sr_mono, x_axis='time', y_axis='log', ax=ax)
ax.set_title("Monophonic Audio: Clean Spectrum")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Frequency (Hz)")

ax = axes[0, 1]
D_poly = librosa.amplitude_to_db(np.abs(librosa.stft(y_poly)), ref=np.max)
librosa.display.specshow(D_poly, sr=sr_poly, x_axis='time', y_axis='log', ax=ax)
ax.set_title("Polyphonic Audio: Complex Spectrum")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Frequency (Hz)")

# 2. Pitch tracking with confidence - MONOPHONIC
ax = axes[1, 0]
# Use original frequencies (not filtered) for scatter plot
valid_mask_mono = confidence_mono >= 0.8
scatter = ax.scatter(t_mono[valid_mask_mono], 
                     f_mono_original[valid_mask_mono], 
                     c=confidence_mono[valid_mask_mono], 
                     cmap='viridis', s=10, alpha=0.7)
# Plot low confidence points in gray
if np.sum(~valid_mask_mono) > 0:
    ax.scatter(t_mono[~valid_mask_mono], 
               f_mono_original[~valid_mask_mono], 
               c='gray', s=5, alpha=0.3, label='Low confidence')
plt.colorbar(scatter, ax=ax, label='Confidence')
ax.set_title("Monophonic: High-Confidence Tracking")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Frequency (Hz)")
ax.set_ylim(50, 1000)  # Set reasonable frequency limits
if np.sum(~valid_mask_mono) > 0:
    ax.legend()

# 3. Pitch tracking with confidence - POLYPHONIC
ax = axes[1, 1]
valid_mask_poly = confidence_poly >= 0.8
scatter = ax.scatter(t_poly[valid_mask_poly], 
                     f_poly_original[valid_mask_poly], 
                     c=confidence_poly[valid_mask_poly], 
                     cmap='viridis', s=10, alpha=0.7)
# Plot low confidence points in gray
if np.sum(~valid_mask_poly) > 0:
    ax.scatter(t_poly[~valid_mask_poly], 
               f_poly_original[~valid_mask_poly], 
               c='gray', s=5, alpha=0.3, label='Low confidence')
plt.colorbar(scatter, ax=ax, label='Confidence')
ax.set_title("Polyphonic: Low-Confidence Erratic Tracking")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Frequency (Hz)")
ax.set_ylim(50, 1000)  # Set same limits for comparison
if np.sum(~valid_mask_poly) > 0:
    ax.legend()

plt.tight_layout()
plt.show()

# Print quantitative analysis
print("=== PITCH TRACKING ANALYSIS ===")
print(f"Monophonic Audio ({mono_path}):")
print(f"  - Total frames: {len(t_mono)}")
print(f"  - High-confidence frames: {np.sum(valid_mask_mono)} ({(np.sum(valid_mask_mono)/len(t_mono))*100:.1f}%)")
print(f"  - Mean confidence: {np.mean(confidence_mono):.3f}")
print(f"  - Pitch range: {np.min(f_mono_original[valid_mask_mono]):.1f} - {np.max(f_mono_original[valid_mask_mono]):.1f} Hz")

print(f"\nPolyphonic Audio ({poly_path}):")
print(f"  - Total frames: {len(t_poly)}")
print(f"  - High-confidence frames: {np.sum(valid_mask_poly)} ({(np.sum(valid_mask_poly)/len(t_poly))*100:.1f}%)")
print(f"  - Mean confidence: {np.mean(confidence_poly):.3f}")
if np.sum(valid_mask_poly) > 0:
    print(f"  - Pitch range: {np.min(f_poly_original[valid_mask_poly]):.1f} - {np.max(f_poly_original[valid_mask_poly]):.1f} Hz")
else:
    print(f"  - Pitch range: No valid frames")

# Calculate pitch stability (rate of large jumps)
if np.sum(valid_mask_mono) > 1:
    mono_jumps = np.sum(np.abs(np.diff(f_mono_original[valid_mask_mono])) > 100)
    print(f"  - Large pitch jumps (>100Hz): {mono_jumps}")

if np.sum(valid_mask_poly) > 1:
    poly_jumps = np.sum(np.abs(np.diff(f_poly_original[valid_mask_poly])) > 100)
    print(f"  - Large pitch jumps (>100Hz): {poly_jumps}")

print("\n=== KEY INSIGHT ===")
print("CREPE pitch tracking performs reliably on monophonic audio with high confidence")
print("but fails on polyphonic audio, producing erratic estimates with low confidence.")
print("This demonstrates the need for specialized multi-pitch estimation algorithms")
print("for polyphonic music analysis.")