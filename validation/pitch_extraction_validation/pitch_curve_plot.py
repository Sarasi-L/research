import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ---------- SETTINGS ----------
BASE_DIR = Path(__file__).resolve().parent
plots_folder = BASE_DIR / "plots"
os.makedirs(plots_folder, exist_ok=True)

# ---------- EXAMPLE DATA ----------
# Dummy pitch curve (replace with actual extract_pitch output if needed)
time = np.linspace(0, 3, 300)  # 3-second audio, 300 frames
frequency = 440 + 5*np.sin(2*np.pi*2*time)  # pitch around A4
confidence = np.clip(np.random.normal(0.9, 0.05, size=time.shape), 0, 1)  # confidence

# ---------- PLOT ----------
plt.figure(figsize=(10,4))
plt.plot(time, frequency, label='Extracted Pitch', color='blue')
plt.scatter(time, frequency, c=confidence, cmap='viridis', s=20, label='Confidence')
plt.xlabel("Time (s)")
plt.ylabel("Frequency (Hz)")
plt.title("CREPE Pitch Curve Example (NSynth)")
plt.colorbar(label='Confidence')
plt.legend()
plt.tight_layout()

# ---------- SAVE ----------
plot_path = os.path.join(plots_folder, "pitch_curve_example.png")
plt.savefig(plot_path)
plt.close()
print(f"✅ Pitch curve plot saved at: {plot_path}")
