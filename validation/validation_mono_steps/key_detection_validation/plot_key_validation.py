import os
import matplotlib.pyplot as plt
import numpy as np

from validation.key_detection_validation.run_key_validation import (
    key_confidences,
    fallback_used
)

PLOT_DIR = "validation/key_detection_validation/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ------------------------------
# 1️⃣ Confidence Distribution
# ------------------------------
plt.figure(figsize=(6,4))
plt.hist(key_confidences, bins=20)
plt.xlabel("Key Detection Confidence")
plt.ylabel("Count")
plt.title("Key Detection Confidence Distribution")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "key_confidence_hist.png"))
plt.close()

# ------------------------------
# 2️⃣ Fallback Usage
# ------------------------------
fallback_rate = [fallback_used.count(False), fallback_used.count(True)]

plt.figure(figsize=(4,4))
plt.bar(["Normal", "Fallback"], fallback_rate)
plt.ylabel("Count")
plt.title("Confidence Gating Usage")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "fallback_usage.png"))
plt.close()

print("✅ Key detection validation plots saved.")
