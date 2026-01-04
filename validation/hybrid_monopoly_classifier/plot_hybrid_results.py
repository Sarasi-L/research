# validation/hybrid_monopoly_classifier/plot_results.py

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from pathlib import Path
import os

# =====================================================
# CONFIG
# =====================================================
BASE_DIR = Path(__file__).resolve().parent
PRED_CSV = BASE_DIR / "predictions_hybrid.csv"
OUTPUT_DIR = BASE_DIR / "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =====================================================
# LOAD DATA
# =====================================================
df = pd.read_csv(PRED_CSV)

# Normalize labels
label_map = {
    "mono": "monophonic",
    "poly": "polyphonic"
}

df["true_label_norm"] = df["true_label"].replace(label_map)
df["pred_label_norm"] = df["predicted_label"].replace(label_map)

df_eval = df[df["true_label_norm"].isin(["monophonic", "polyphonic"])]
df_amb = df[df["true_label"] == "ambiguous"]

# =====================================================
# 1️⃣ Confusion Matrix
# =====================================================
labels = ["monophonic", "polyphonic"]
cm = confusion_matrix(
    df_eval["true_label_norm"],
    df_eval["pred_label_norm"],
    labels=labels
)

plt.figure(figsize=(5, 4))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=["Mono", "Poly"],
    yticklabels=["Mono", "Poly"]
)
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix – Hybrid Classifier")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "confusion_matrix.png", dpi=300)
plt.show()

# =====================================================
# 2️⃣ Accuracy Comparison
# =====================================================
accuracies = [82, 99, 96]
models = ["CREPE", "CRNN", "Hybrid"]

plt.figure(figsize=(6, 4))
sns.barplot(x=models, y=accuracies)
plt.ylim(0, 100)
plt.ylabel("Accuracy (%)")
plt.title("Classifier Accuracy Comparison")

for i, acc in enumerate(accuracies):
    plt.text(i, acc + 1, f"{acc}%", ha="center")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "accuracy_comparison.png", dpi=300)
plt.show()

# =====================================================
# 3️⃣ Ambiguous Confidence Histogram
# =====================================================
plt.figure(figsize=(7, 4))
sns.histplot(df_amb["confidence"], bins=10, kde=True)
plt.xlabel("Confidence")
plt.ylabel("Number of Samples")
plt.title("Confidence Distribution – Ambiguous Samples")
plt.xlim(0, 1)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "ambiguous_confidence_hist.png", dpi=300)
plt.show()

# =====================================================
# 4️⃣ Ambiguous Confidence Scatter
# =====================================================
plt.figure(figsize=(7, 4))
plt.scatter(range(len(df_amb)), df_amb["confidence"], alpha=0.8)
plt.xlabel("Sample Index")
plt.ylabel("Hybrid Confidence")
plt.title("Hybrid Confidence on Ambiguous Samples")
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "ambiguous_confidence_scatter.png", dpi=300)
plt.show()

print(f"✅ All individual plots saved in: {OUTPUT_DIR}")




# import pandas as pd
# import matplotlib.pyplot as plt
# import seaborn as sns
# from sklearn.metrics import confusion_matrix
# from pathlib import Path

# # ===============================
# # Paths
# # ===============================
# BASE_DIR = Path(__file__).resolve().parent
# PRED_CSV = BASE_DIR / "predictions_hybrid.csv"
# PLOT_DIR = BASE_DIR / "plots"
# PLOT_DIR.mkdir(exist_ok=True)

# # ===============================
# # Load data
# # ===============================
# df = pd.read_csv(PRED_CSV)

# # -------------------------------
# # Normalize labels
# # -------------------------------
# label_map = {
#     "mono": "monophonic",
#     "poly": "polyphonic"
# }

# df["true_label_norm"] = df["true_label"].replace(label_map)
# df["pred_label_norm"] = df["predicted_label"].replace(label_map)

# mono_poly_df = df[df["true_label_norm"].isin(["monophonic", "polyphonic"])]
# ambiguous_df = df[df["true_label"] == "ambiguous"]

# # ===============================
# # Confusion Matrix
# # ===============================
# labels = ["monophonic", "polyphonic"]
# cm = confusion_matrix(
#     mono_poly_df["true_label_norm"],
#     mono_poly_df["pred_label_norm"],
#     labels=labels
# )

# # ===============================
# # Plotting
# # ===============================
# sns.set(style="whitegrid")

# fig, axes = plt.subplots(2, 2, figsize=(16, 12))
# fig.suptitle(
#     "Hybrid Mono/Poly Classifier – Research Evaluation",
#     fontsize=18,
#     fontweight="bold"
# )

# # ---- 1. Confusion Matrix ----
# sns.heatmap(
#     cm,
#     annot=True,
#     fmt="d",
#     cmap="Blues",
#     xticklabels=["Mono", "Poly"],
#     yticklabels=["Mono", "Poly"],
#     ax=axes[0, 0]
# )
# axes[0, 0].set_title("Confusion Matrix")
# axes[0, 0].set_xlabel("Predicted Label")
# axes[0, 0].set_ylabel("True Label")

# # ---- 2. Ambiguous Confidence Distribution ----
# sns.histplot(
#     ambiguous_df["confidence"],
#     bins=10,
#     kde=True,
#     ax=axes[0, 1]
# )
# axes[0, 1].set_title("Confidence Distribution (Ambiguous Samples)")
# axes[0, 1].set_xlabel("Confidence")
# axes[0, 1].set_ylabel("Sample Count")

# # ---- 3. Ambiguous Confidence Scatter ----
# axes[1, 0].scatter(
#     range(len(ambiguous_df)),
#     ambiguous_df["confidence"],
#     alpha=0.8
# )
# axes[1, 0].set_ylim(0, 1.05)
# axes[1, 0].set_title("Hybrid Confidence Scatter (Ambiguous)")
# axes[1, 0].set_xlabel("Sample Index")
# axes[1, 0].set_ylabel("Confidence")

# # ---- 4. Accuracy Comparison ----
# accuracy_data = pd.DataFrame({
#     "Model": ["CREPE", "CRNN", "Hybrid"],
#     "Accuracy (%)": [82, 99, 96]
# })

# sns.barplot(
#     data=accuracy_data,
#     x="Model",
#     y="Accuracy (%)",
#     ax=axes[1, 1]
# )
# axes[1, 1].set_ylim(0, 100)
# axes[1, 1].set_title("Model Accuracy Comparison")

# # ===============================
# # Layout & Save
# # ===============================
# plt.subplots_adjust(
#     left=0.07,
#     right=0.95,
#     top=0.90,
#     bottom=0.08,
#     hspace=0.35,
#     wspace=0.25
# )

# output_path = PLOT_DIR / "hybrid_model_evaluation.png"
# plt.savefig(output_path, dpi=300)
# plt.show()

# print(f"✅ Main evaluation plot saved to: {output_path}")