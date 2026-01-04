# validation/hybrid_monopoly_classifier/bootstrap_ci.py

import pandas as pd
import numpy as np
from pathlib import Path

# ===============================
# CONFIG
# ===============================
N_BOOTSTRAP = 1000
CONF_LEVEL = 0.95

BASE_DIR = Path(__file__).resolve().parent
PRED_CSV = BASE_DIR / "predictions_hybrid.csv"

# ===============================
# LOAD DATA
# ===============================
df = pd.read_csv(PRED_CSV)

# Remove ambiguous samples
df = df[df["true_label"] != "ambiguous"]

# ✅ STRICT NORMALIZATION
def normalize(label):
    if label in ["mono", "monophonic"]:
        return "monophonic"
    if label in ["poly", "polyphonic"]:
        return "polyphonic"
    return None

df["true_label"] = df["true_label"].apply(normalize)
df["predicted_label"] = df["predicted_label"].apply(normalize)

# Drop any broken rows (safety)
df = df.dropna(subset=["true_label", "predicted_label"])

# ===============================
# BOOTSTRAP
# ===============================
accuracies = []
n = len(df)

for _ in range(N_BOOTSTRAP):
    sample = df.sample(n=n, replace=True)
    acc = (sample["true_label"] == sample["predicted_label"]).mean()
    accuracies.append(acc)

accuracies = np.array(accuracies)

# ===============================
# CONFIDENCE INTERVAL
# ===============================
mean_acc = accuracies.mean()
lower = np.percentile(accuracies, (1 - CONF_LEVEL) / 2 * 100)
upper = np.percentile(accuracies, (1 + CONF_LEVEL) / 2 * 100)

# ===============================
# OUTPUT
# ===============================
print("📊 Bootstrap Accuracy Analysis (Hybrid Classifier)")
print("--------------------------------------------------")
print(f"Samples evaluated: {n}")
print(f"Bootstrap iterations: {N_BOOTSTRAP}")
print(f"Mean accuracy: {mean_acc * 100:.2f}%")
print(f"{int(CONF_LEVEL*100)}% Confidence Interval: "
      f"[{lower * 100:.2f}%, {upper * 100:.2f}%]")
