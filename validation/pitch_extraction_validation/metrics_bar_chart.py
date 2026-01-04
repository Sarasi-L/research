import os
import matplotlib.pyplot as plt
from pathlib import Path

# ---------- SETTINGS ----------
BASE_DIR = Path(__file__).resolve().parent
plots_folder = BASE_DIR / "plots"
os.makedirs(plots_folder, exist_ok=True)

# ---------- DATA ----------
metrics = ['RPA', 'RCA', 'OA']
values = [96.88, 97.41, 96.88]  # Your final CREPE validation results (%)

# ---------- PLOT ----------
plt.figure(figsize=(6,4))
plt.bar(metrics, values, color=['skyblue', 'orange', 'green'])
plt.ylim(0, 100)
plt.ylabel("Accuracy (%)")
plt.title("CREPE Pitch Extraction Validation (NSynth 30 files)")

# Add value labels on top
for i, v in enumerate(values):
    plt.text(i, v + 1, f"{v:.2f}%", ha='center')

plt.tight_layout()

# ---------- SAVE ----------
plot_path = os.path.join(plots_folder, "crepe_pitch_bar.png")
plt.savefig(plot_path)
plt.close()
print(f"✅ Plot saved at: {plot_path}")
