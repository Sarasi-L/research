# validation/tempo_estimation_validation/plot_tempo_results.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ------------------------------
# CONFIG
# ------------------------------
RESULTS_CSV = "validation/tempo_estimation_validation/results/tempo_results.csv"
PLOT_DIR = "validation/tempo_estimation_validation/plots"

os.makedirs(PLOT_DIR, exist_ok=True)

# ------------------------------
# LOAD DATA
# ------------------------------
df = pd.read_csv(RESULTS_CSV)

# Use corrected predictions
df["ABS_ERR"] = abs(df["gt_tempo"] - df["corrected_pred_tempo"])

# ------------------------------
# 1. Scatter plot: GT vs Predicted
# ------------------------------
plt.figure(figsize=(8, 8))
sns.scatterplot(x="gt_tempo", y="corrected_pred_tempo", hue="genre", data=df, alpha=0.7, s=60)
plt.plot([0, 250], [0, 250], "k--", label="Perfect prediction")
plt.xlabel("Ground Truth Tempo (BPM)")
plt.ylabel("Predicted Tempo (BPM)")
plt.title("Tempo Estimation: GT vs Predicted")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "scatter_gt_vs_pred.png"), dpi=300)
plt.close()

# ------------------------------
# 2. Histogram of absolute errors
# ------------------------------
plt.figure(figsize=(8, 5))
sns.histplot(df["ABS_ERR"], bins=30, kde=True, color="skyblue")
plt.xlabel("Absolute Error (BPM)")
plt.ylabel("Count")
plt.title("Distribution of Tempo Estimation Errors")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "hist_abs_error.png"), dpi=300)
plt.close()

# ------------------------------
# 3. Boxplot of absolute errors per genre
# ------------------------------
plt.figure(figsize=(10, 6))
sns.boxplot(x="genre", y="ABS_ERR", data=df, palette="Set2")
plt.xlabel("Genre")
plt.ylabel("Absolute Error (BPM)")
plt.title("Tempo Estimation Errors by Genre")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "box_abs_error_genre.png"), dpi=300)
plt.close()

# ------------------------------
# 4. Accuracy bar plot per genre
# ------------------------------
accuracy_df = df.groupby("genre")[["correct_4bpm", "correct_8bpm"]].mean().reset_index()
accuracy_df_melted = accuracy_df.melt(id_vars="genre", var_name="Threshold", value_name="Accuracy")

plt.figure(figsize=(10, 6))
sns.barplot(x="genre", y="Accuracy", hue="Threshold", data=accuracy_df_melted, palette="Set1")
plt.ylim(0, 1)
plt.ylabel("Accuracy")
plt.title("Tempo Estimation Accuracy per Genre")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "accuracy_genre.png"), dpi=300)
plt.close()

print(f"[INFO] Plots saved in {PLOT_DIR}")
