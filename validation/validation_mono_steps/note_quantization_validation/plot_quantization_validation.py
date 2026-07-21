import os
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# ---------------------------------------
# IMPORT VALIDATION RESULTS (NO RE-RUN)
# ---------------------------------------
from validation.note_quantization_validation.run_quantization_stats import (
    raw_beats,
    quantized_beats,
    duration_names,
    tie_flags
)

# ---------------------------------------
# SETUP
# ---------------------------------------
PLOT_DIR = "validation/note_quantization_validation/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

raw_beats = np.array(raw_beats)
quantized_beats = np.array(quantized_beats)

# ---------------------------------------
# 1️⃣ Duration Snapping Error Distribution
# ---------------------------------------
errors = np.abs(raw_beats - quantized_beats)

plt.figure(figsize=(6,4))
plt.hist(errors, bins=30)
plt.xlabel("Snapping Error (beats)")
plt.ylabel("Count")
plt.title("Quantization Snapping Error Distribution")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "quantization_error_hist.png"))
plt.close()

# ---------------------------------------
# 2️⃣ Quantized Note Value Frequency
# ---------------------------------------
counts = Counter(duration_names)

plt.figure(figsize=(7,4))
plt.bar(counts.keys(), counts.values())
plt.xlabel("Note Type")
plt.ylabel("Count")
plt.title("Quantized Note Value Distribution")
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "quantized_note_distribution.png"))
plt.close()

# ---------------------------------------
# 3️⃣ Raw vs Quantized Duration Scatter
# ---------------------------------------
plt.figure(figsize=(5,5))
plt.scatter(raw_beats, quantized_beats, s=20)
plt.xlabel("Raw Duration (beats)")
plt.ylabel("Quantized Duration (beats)")
plt.title("Raw vs Quantized Duration Mapping")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "raw_vs_quantized_scatter.png"))
plt.close()

# ---------------------------------------
# 4️⃣ Tie Usage Ratio
# ---------------------------------------
tie_counts = Counter(tie_flags)

plt.figure(figsize=(4,4))
plt.bar(["No Tie", "Tied"], [tie_counts[False], tie_counts[True]])
plt.ylabel("Count")
plt.title("Tie Usage in Quantization")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "tie_usage.png"))
plt.close()

# ---------------------------------------
print("✅ Quantization validation plots saved to /plots")
