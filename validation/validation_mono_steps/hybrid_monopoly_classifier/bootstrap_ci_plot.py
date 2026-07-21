import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "predictions_hybrid.csv"
PLOT_DIR = BASE_DIR / "plots"
PLOT_DIR.mkdir(exist_ok=True)

BOOTSTRAP_ITER = 1000

df = pd.read_csv(CSV_PATH)

# Keep only mono/poly for accuracy
df = df[df["true_label"].isin(["mono", "poly", "monophonic", "polyphonic"])]


label_map = {
    "mono": "monophonic",
    "poly": "polyphonic"
}

df["true_norm"] = df["true_label"].map(label_map).fillna(df["true_label"])
df["pred_norm"] = df["predicted_label"]

y_true = df["true_norm"].values
y_pred = df["pred_norm"].values


# BOOTSTRAP SAMPLING
rng = np.random.default_rng(42)
accuracies = []

n = len(y_true)

for _ in range(BOOTSTRAP_ITER):
    idx = rng.integers(0, n, n)
    acc = np.mean(y_true[idx] == y_pred[idx])
    accuracies.append(acc)

accuracies = np.array(accuracies)

mean_acc = accuracies.mean()
ci_low = np.percentile(accuracies, 2.5)
ci_high = np.percentile(accuracies, 97.5)


plt.figure(figsize=(8, 5))

plt.hist(accuracies, bins=30, density=True, alpha=0.6)
plt.axvline(mean_acc, linestyle="--", linewidth=2, label=f"Mean = {mean_acc:.2f}")
plt.axvline(ci_low, linestyle=":", linewidth=2, label=f"95% CI Low = {ci_low:.2f}")
plt.axvline(ci_high, linestyle=":", linewidth=2, label=f"95% CI High = {ci_high:.2f}")

plt.xlabel("Accuracy")
plt.ylabel("Density")
plt.title("Bootstrap Accuracy Distribution (Hybrid Classifier)")
plt.legend()

output_path = PLOT_DIR / "bootstrap_accuracy_ci.png"
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.show()

print(" Bootstrap Accuracy CI Plot")
print("----------------------------------")
print(f"Mean Accuracy: {mean_acc*100:.2f}%")
print(f"95% CI: [{ci_low*100:.2f}%, {ci_high*100:.2f}%]")
print(f"Saved to: {output_path}")
