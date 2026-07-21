# validation/hybrid_monopoly_classifier/mcnemar_test.py

import pandas as pd
from statsmodels.stats.contingency_tables import mcnemar
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CRNN_CSV = BASE_DIR / "predictions_crnn.csv"
HYBRID_CSV = BASE_DIR / "predictions_hybrid.csv"

df_crnn = pd.read_csv(CRNN_CSV)
df_hybrid = pd.read_csv(HYBRID_CSV)

df = df_crnn.merge(
    df_hybrid,
    on="filename",
    suffixes=("_crnn", "_hybrid")
)

# Sanity check
if not (df["true_label_crnn"] == df["true_label_hybrid"]).all():
    raise ValueError("True labels do not match between CRNN and Hybrid predictions")

# Use a single ground-truth column
df["true_label"] = df["true_label_crnn"]

# Remove ambiguous samples
df = df[df["true_label"] != "ambiguous"]

# Correctness flags
df["crnn_correct"] = df["predicted_label_crnn"] == df["true_label"]
df["hybrid_correct"] = df["predicted_label_hybrid"] == df["true_label"]

# McNemar contingency counts
b = ((~df["crnn_correct"]) & (df["hybrid_correct"])).sum()
c = ((df["crnn_correct"]) & (~df["hybrid_correct"])).sum()

table = [[0, b],
         [c, 0]]

# McNemar Test
result = mcnemar(table, exact=True)

print("\n McNemar Test: CRNN vs Hybrid")
print("--------------------------------")
print(f"b (CRNN wrong, Hybrid correct): {b}")
print(f"c (CRNN correct, Hybrid wrong): {c}")
print(f"p-value: {result.pvalue:.6f}")

if result.pvalue < 0.05:
    print("Statistically significant difference (p < 0.05)")
else:
    print("Difference is NOT statistically significant")
