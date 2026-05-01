# visualize_results.py

import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

ROOT        = Path(__file__).resolve().parent
INPUT_CSV   = ROOT / "evaluation_results.csv"
PLOT_DIR    = ROOT / "evaluation_plots"
PLOT_DIR.mkdir(exist_ok=True)

# Publication style settings
STYLE = {
    "figure.facecolor":     "#FFFFFF",
    "axes.facecolor":       "#F8F9FA",
    "axes.edgecolor":       "#CCCCCC",
    "axes.grid":            True,
    "grid.color":           "#E0E0E0",
    "grid.linestyle":       "--",
    "grid.linewidth":       0.7,
    "font.family":          "DejaVu Sans",
    "font.size":            11,
    "axes.titlesize":       13,
    "axes.titleweight":     "bold",
    "axes.labelsize":       11,
    "xtick.labelsize":      9,
    "ytick.labelsize":      9,
    "legend.fontsize":      10,
    "legend.framealpha":    0.9,
    "figure.dpi":           150,
    "savefig.dpi":          300,
    "savefig.bbox":         "tight",
    "savefig.pad_inches":   0.15,
}

# Colour palette (colour-blind friendly)
C_MIDI   = "#2196F3"   # blue
C_XML    = "#4CAF50"   # green
C_OFFSET = "#FF9800"   # orange
C_VEL    = "#9C27B0"   # purple
C_F1     = "#F44336"   # red

matplotlib.rcParams.update(STYLE)


# ============================================================
# LOAD CSV
# ============================================================

def load_results(csv_path):
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (float(v) if k != "song" else v)
                         for k, v in row.items()})
    return rows


# ============================================================
# HELPER
# ============================================================

def savefig(name):
    path = PLOT_DIR / f"{name}.png"
    plt.savefig(path)
    plt.close()
    print(f"  Saved: {path.name}")


def song_labels(songs, max_chars=18):
    """Shorten long song names for tick labels."""
    return [s[:max_chars] + "…" if len(s) > max_chars else s for s in songs]


# ============================================================
# PLOT 1 – MIDI Precision / Recall / F1  (grouped bar)
# ============================================================

def plot_midi_prf(rows):
    songs  = [r["song"] for r in rows]
    labels = song_labels(songs)
    x      = np.arange(len(songs))
    w      = 0.26

    fig, ax = plt.subplots(figsize=(max(10, len(songs) * 0.8), 5))

    b1 = ax.bar(x - w,   [r["midi_precision"] for r in rows], w,
                label="Precision", color=C_MIDI,   alpha=0.85)
    b2 = ax.bar(x,       [r["midi_recall"]    for r in rows], w,
                label="Recall",    color=C_OFFSET, alpha=0.85)
    b3 = ax.bar(x + w,   [r["midi_f1"]        for r in rows], w,
                label="F1",        color=C_F1,     alpha=0.85)

    # Mean lines
    for vals, color, lbl in [
        ([r["midi_precision"] for r in rows], C_MIDI,   "Mean Precision"),
        ([r["midi_recall"]    for r in rows], C_OFFSET, "Mean Recall"),
        ([r["midi_f1"]        for r in rows], C_F1,     "Mean F1"),
    ]:
        ax.axhline(np.mean(vals), color=color, linewidth=1.4,
                   linestyle=":", alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Score")
    ax.set_title("MIDI Evaluation — Precision, Recall, F1 per Song")
    ax.legend(loc="upper right")
    savefig("01_midi_precision_recall_f1")


# ============================================================
# PLOT 2 – XML Precision / Recall / F1  (grouped bar)
# ============================================================

def plot_xml_prf(rows):
    # Skip if no XML results
    if all(r["xml_f1"] == 0 for r in rows):
        print("  [skip] No XML results found.")
        return

    songs  = [r["song"] for r in rows]
    labels = song_labels(songs)
    x      = np.arange(len(songs))
    w      = 0.26

    fig, ax = plt.subplots(figsize=(max(10, len(songs) * 0.8), 5))

    ax.bar(x - w, [r["xml_precision"] for r in rows], w,
           label="Precision", color=C_XML,    alpha=0.85)
    ax.bar(x,     [r["xml_recall"]    for r in rows], w,
           label="Recall",    color=C_OFFSET, alpha=0.85)
    ax.bar(x + w, [r["xml_f1"]        for r in rows], w,
           label="F1",        color=C_F1,     alpha=0.85)

    for vals, color in [
        ([r["xml_precision"] for r in rows], C_XML),
        ([r["xml_recall"]    for r in rows], C_OFFSET),
        ([r["xml_f1"]        for r in rows], C_F1),
    ]:
        ax.axhline(np.mean(vals), color=color, linewidth=1.4,
                   linestyle=":", alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Score")
    ax.set_title("XML / MusicXML Evaluation — Precision, Recall, F1 per Song")
    ax.legend(loc="upper right")
    savefig("02_xml_precision_recall_f1")


# ============================================================
# PLOT 3 – Offset & Velocity Accuracy  (line plot)
# ============================================================

def plot_offset_velocity(rows):
    songs  = [r["song"] for r in rows]
    labels = song_labels(songs)
    x      = np.arange(len(songs))

    fig, ax = plt.subplots(figsize=(max(10, len(songs) * 0.8), 5))

    ax.plot(x, [r["offset_accuracy"]   for r in rows], "o-",
            color=C_OFFSET, linewidth=2, markersize=5,
            label="Offset Accuracy")
    ax.plot(x, [r["velocity_accuracy"] for r in rows], "s-",
            color=C_VEL,    linewidth=2, markersize=5,
            label="Velocity Accuracy (±20 %)")

    ax.axhline(np.mean([r["offset_accuracy"]   for r in rows]),
               color=C_OFFSET, linewidth=1.3, linestyle=":", alpha=0.7,
               label=f"Mean Offset  {np.mean([r['offset_accuracy'] for r in rows]):.3f}")
    ax.axhline(np.mean([r["velocity_accuracy"] for r in rows]),
               color=C_VEL,    linewidth=1.3, linestyle=":", alpha=0.7,
               label=f"Mean Velocity {np.mean([r['velocity_accuracy'] for r in rows]):.3f}")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Accuracy")
    ax.set_title("MIDI Offset & Velocity Accuracy per Song")
    ax.legend(loc="upper right")
    savefig("03_offset_velocity_accuracy")


# ============================================================
# PLOT 4 – MIDI vs XML F1 Comparison  (side-by-side bars)
# ============================================================

def plot_midi_vs_xml_f1(rows):
    has_xml = any(r["xml_f1"] > 0 for r in rows)
    songs   = [r["song"] for r in rows]
    labels  = song_labels(songs)
    x       = np.arange(len(songs))
    w       = 0.38 if has_xml else 0.55

    fig, ax = plt.subplots(figsize=(max(10, len(songs) * 0.8), 5))

    ax.bar(x - w / 2 if has_xml else x,
           [r["midi_f1"] for r in rows], w,
           label="MIDI F1", color=C_MIDI, alpha=0.85)

    if has_xml:
        ax.bar(x + w / 2, [r["xml_f1"] for r in rows], w,
               label="XML F1", color=C_XML, alpha=0.85)

    ax.axhline(np.mean([r["midi_f1"] for r in rows]),
               color=C_MIDI, linewidth=1.4, linestyle=":", alpha=0.7)
    if has_xml:
        ax.axhline(np.mean([r["xml_f1"] for r in rows]),
                   color=C_XML, linewidth=1.4, linestyle=":", alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("F1 Score")
    ax.set_title("MIDI F1 vs XML F1 per Song")
    ax.legend(loc="upper right")
    savefig("04_midi_vs_xml_f1")


# ============================================================
# PLOT 5 – Summary Box Plots
# ============================================================

def plot_summary_boxplots(rows):
    has_xml = any(r["xml_f1"] > 0 for r in rows)

    metrics = [
        ("midi_precision", "MIDI\nPrecision",  C_MIDI),
        ("midi_recall",    "MIDI\nRecall",     C_MIDI),
        ("midi_f1",        "MIDI\nF1",         C_MIDI),
        ("offset_accuracy","Offset\nAccuracy", C_OFFSET),
        ("velocity_accuracy","Velocity\nAccuracy",C_VEL),
    ]
    if has_xml:
        metrics += [
            ("xml_precision", "XML\nPrecision", C_XML),
            ("xml_recall",    "XML\nRecall",    C_XML),
            ("xml_f1",        "XML\nF1",        C_XML),
        ]

    data   = [[r[k] for r in rows] for k, *_ in metrics]
    labels = [lbl  for _, lbl, _ in metrics]
    colors = [col  for _, _, col  in metrics]

    fig, ax = plt.subplots(figsize=(len(metrics) * 1.5 + 2, 6))

    bp = ax.boxplot(data, patch_artist=True, notch=False,
                    medianprops=dict(color="black", linewidth=2),
                    whiskerprops=dict(linewidth=1.2),
                    capprops=dict(linewidth=1.2),
                    flierprops=dict(marker="o", markersize=4,
                                   markerfacecolor="gray", alpha=0.5))

    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(-0.05, 1.1)
    ax.set_ylabel("Score")
    ax.set_title("Distribution of All Evaluation Metrics (Box Plot)")

    # Legend patches
    patches = [
        mpatches.Patch(facecolor=C_MIDI,   alpha=0.75, label="MIDI"),
        mpatches.Patch(facecolor=C_OFFSET, alpha=0.75, label="Offset"),
        mpatches.Patch(facecolor=C_VEL,    alpha=0.75, label="Velocity"),
    ]
    if has_xml:
        patches.append(mpatches.Patch(facecolor=C_XML, alpha=0.75, label="XML"))
    ax.legend(handles=patches, loc="lower right")

    savefig("05_summary_boxplots")


# ============================================================
# PLOT 6 – Score Heatmap  (songs × metrics)
# ============================================================

def plot_heatmap(rows):
    metric_keys = [
        "midi_precision", "midi_recall", "midi_f1",
        "offset_accuracy", "velocity_accuracy",
        "xml_precision", "xml_recall", "xml_f1",
    ]
    metric_labels = [
        "MIDI Prec.", "MIDI Rec.", "MIDI F1",
        "Offset Acc.", "Vel. Acc.",
        "XML Prec.", "XML Rec.", "XML F1",
    ]
    songs  = [r["song"] for r in rows]
    labels = song_labels(songs, max_chars=22)

    matrix = np.array([[r[k] for k in metric_keys] for r in rows])

    fig_h = max(5, len(songs) * 0.45 + 2)
    fig, ax = plt.subplots(figsize=(11, fig_h))

    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)

    ax.set_xticks(range(len(metric_keys)))
    ax.set_xticklabels(metric_labels, rotation=35, ha="right", fontsize=10)
    ax.set_yticks(range(len(songs)))
    ax.set_yticklabels(labels, fontsize=9)

    # Annotate cells
    for i in range(len(songs)):
        for j in range(len(metric_keys)):
            val = matrix[i, j]
            txt_color = "black" if 0.25 < val < 0.75 else "white"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color=txt_color, fontweight="bold")

    plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02, label="Score")
    ax.set_title("Evaluation Score Heatmap (Songs × Metrics)")
    plt.tight_layout()
    savefig("06_score_heatmap")


# ============================================================
# PLOT 7 – Average Scores Summary Bar
# ============================================================

def plot_average_summary(rows):
    has_xml = any(r["xml_f1"] > 0 for r in rows)

    metrics = [
        ("midi_precision",   "MIDI\nPrecision",    C_MIDI),
        ("midi_recall",      "MIDI\nRecall",        C_MIDI),
        ("midi_f1",          "MIDI\nF1",            C_MIDI),
        ("offset_accuracy",  "Offset\nAccuracy",    C_OFFSET),
        ("velocity_accuracy","Velocity\nAccuracy",  C_VEL),
    ]
    if has_xml:
        metrics += [
            ("xml_precision", "XML\nPrecision", C_XML),
            ("xml_recall",    "XML\nRecall",    C_XML),
            ("xml_f1",        "XML\nF1",        C_XML),
        ]

    keys   = [k   for k, _, _   in metrics]
    labels = [lbl for _, lbl, _ in metrics]
    colors = [col for _, _, col in metrics]
    means  = [np.mean([r[k] for r in rows]) for k in keys]
    stds   = [np.std([r[k]  for r in rows]) for k in keys]

    x   = np.arange(len(keys))
    fig, ax = plt.subplots(figsize=(len(keys) * 1.5 + 2, 6))

    bars = ax.bar(x, means, color=colors, alpha=0.85,
                  yerr=stds, capsize=5,
                  error_kw=dict(elinewidth=1.5, ecolor="black", alpha=0.6))

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f"{mean:.3f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Mean Score  (± std)")
    ax.set_title("Average Evaluation Scores Across All Songs  (error bars = std dev)")

    patches = [
        mpatches.Patch(facecolor=C_MIDI,   alpha=0.85, label="MIDI"),
        mpatches.Patch(facecolor=C_OFFSET, alpha=0.85, label="Offset"),
        mpatches.Patch(facecolor=C_VEL,    alpha=0.85, label="Velocity"),
    ]
    if has_xml:
        patches.append(mpatches.Patch(facecolor=C_XML, alpha=0.85, label="XML"))
    ax.legend(handles=patches, loc="upper right")

    savefig("07_average_summary")


# ============================================================
# PLOT 8 – Predicted Structure (Notes, Chords, Measures)
# ============================================================

def plot_xml_structure(rows):
    has_struct = any(r["pred_notes"] > 0 for r in rows)
    if not has_struct:
        print("  [skip] No XML structure data.")
        return

    songs  = [r["song"] for r in rows]
    labels = song_labels(songs)
    x      = np.arange(len(songs))
    w      = 0.28

    fig, ax = plt.subplots(figsize=(max(10, len(songs) * 0.8), 5))

    ax.bar(x - w, [r["pred_notes"]    for r in rows], w,
           label="Predicted Notes",   color=C_MIDI,   alpha=0.85)
    ax.bar(x,     [r["pred_chords"]   for r in rows], w,
           label="Predicted Chords",  color=C_XML,    alpha=0.85)
    ax.bar(x + w, [r["pred_measures"] for r in rows], w,
           label="Predicted Measures",color=C_OFFSET, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("Count")
    ax.set_title("Predicted MusicXML Structure — Notes, Chords, Measures per Song")
    ax.legend(loc="upper right")
    savefig("08_xml_structure")


# ============================================================
# PLOT 9 – MIDI F1 vs XML F1  Scatter
# ============================================================

def plot_scatter_midi_vs_xml(rows):
    has_xml = any(r["xml_f1"] > 0 for r in rows)
    if not has_xml:
        print("  [skip] No XML F1 data for scatter.")
        return

    midi_f1 = [r["midi_f1"] for r in rows]
    xml_f1  = [r["xml_f1"]  for r in rows]
    songs   = [r["song"]    for r in rows]

    fig, ax = plt.subplots(figsize=(6, 6))

    sc = ax.scatter(midi_f1, xml_f1, c=range(len(rows)),
                    cmap="tab20", s=80, zorder=3, edgecolors="white", linewidths=0.5)

    # Diagonal reference
    ax.plot([0, 1], [0, 1], "--", color="#AAAAAA", linewidth=1.2, label="y = x")

    # Annotate points
    for i, song in enumerate(songs):
        ax.annotate(song_labels([song])[0],
                    (midi_f1[i], xml_f1[i]),
                    fontsize=7, alpha=0.8,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("MIDI F1")
    ax.set_ylabel("XML F1")
    ax.set_title("MIDI F1 vs XML F1 Correlation")
    ax.legend()
    savefig("09_scatter_midi_vs_xml_f1")


# ============================================================
# MAIN
# ============================================================

def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"CSV not found: {INPUT_CSV}\n"
            "Run the evaluation script first."
        )

    rows = load_results(INPUT_CSV)
    print(f"\nLoaded {len(rows)} songs from {INPUT_CSV.name}")
    print(f"Saving plots to: {PLOT_DIR}\n")

    plot_midi_prf(rows)
    plot_xml_prf(rows)
    plot_offset_velocity(rows)
    plot_midi_vs_xml_f1(rows)
    plot_summary_boxplots(rows)
    plot_heatmap(rows)
    plot_average_summary(rows)
    plot_xml_structure(rows)
    plot_scatter_midi_vs_xml(rows)

    print(f"\nDone. {len(list(PLOT_DIR.glob('*.png')))} plots saved to: {PLOT_DIR}")


if __name__ == "__main__":
    main()