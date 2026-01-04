import os
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- SETTINGS ----------
BASE_DIR = Path(__file__).resolve().parent
plots_folder = BASE_DIR / "plots"
os.makedirs(plots_folder, exist_ok=True)

# ---------- DATA ----------
rpa_per_file = [
    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    0.942, 0.957, 1.0, 1.0, 1.0, 0.831, 0.997, 1.0, 0.911, 0.897,
    0.924, 1.0, 0.667, 1.0, 0.979, 1.0, 0.983, 0.977, 1.0, 1.0
]

# ---------- PLOT ----------
plt.figure(figsize=(6,4))
plt.hist(rpa_per_file, bins=10, color='skyblue', edgecolor='black')
plt.xlabel("RPA per file")
plt.ylabel("Number of files")
plt.title("Distribution of Raw Pitch Accuracy (RPA) across 30 NSynth files")
plt.ylim(0, max([rpa_per_file.count(x) for x in rpa_per_file]) + 1)

plt.tight_layout()

# ---------- SAVE ----------
plot_path = os.path.join(plots_folder, "rpa_histogram.png")
plt.savefig(plot_path)
plt.close()
print(f"✅ Histogram saved at: {plot_path}")
