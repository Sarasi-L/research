import os
import matplotlib.pyplot as plt

from validation.note_segmentation_validation.note_segmentation_internal.run_internal_validation import (
    pitch_stds,
    purities,
    durations,
    notes_per_clip
)
  
# ----------------------------------------
# ASSUMED VARIABLES (already computed)
# ----------------------------------------
# pitch_stds       -> list of float (Hz)
# purities         -> list of float (%)
# durations        -> list of float (seconds)
# notes_per_clip   -> list of int

# ----------------------------------------
# Create plots directory
# ----------------------------------------
PLOT_DIR = "plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ----------------------------------------
# 1. Pitch stability distribution
# ----------------------------------------
plt.figure()
plt.hist(pitch_stds, bins=15)
plt.xlabel("Pitch standard deviation (Hz)")
plt.ylabel("Number of clips")
plt.title("Pitch Stability Distribution")
plt.savefig(os.path.join(PLOT_DIR, "pitch_std_distribution.png"))
plt.close()

# ----------------------------------------
# 2. Note purity distribution
# ----------------------------------------
plt.figure()
plt.hist(purities, bins=15)
plt.xlabel("Note purity (%)")
plt.ylabel("Number of clips")
plt.title("Note Purity Distribution")
plt.savefig(os.path.join(PLOT_DIR, "note_purity_distribution.png"))
plt.close()

# ----------------------------------------
# 3. Note duration distribution
# ----------------------------------------
plt.figure()
plt.hist(durations, bins=15)
plt.xlabel("Note duration (seconds)")
plt.ylabel("Number of clips")
plt.title("Note Duration Distribution")
plt.savefig(os.path.join(PLOT_DIR, "note_duration_distribution.png"))
plt.close()

# ----------------------------------------
# 4. Notes per clip distribution
# ----------------------------------------
plt.figure()
plt.hist(notes_per_clip, bins=range(1, max(notes_per_clip) + 2))
plt.xlabel("Notes per clip")
plt.ylabel("Number of clips")
plt.title("Notes per Clip Distribution")
plt.savefig(os.path.join(PLOT_DIR, "notes_per_clip_distribution.png"))
plt.close()

print("✔ All validation plots saved in 'plots/' folder")
