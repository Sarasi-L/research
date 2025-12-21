import crepe
import numpy as np
from pathlib import Path
import shutil

# Target directory inside your project
TARGET_DIR = Path("models/crepe")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

print("[INFO] Triggering CREPE model download (small)...")

# Dummy audio forces model download
dummy_audio = np.zeros(16000, dtype=np.float32)

crepe.predict(
    dummy_audio,
    16000,
    model_capacity="small",
    step_size=100,
    viterbi=False,
    verbose=0
)

# 🔍 Correct CREPE model location (Keras cache)
KERAS_MODELS = Path.home() / ".keras" / "models"

# Search for CREPE small model
matches = list(KERAS_MODELS.glob("crepe*small*.h5"))

if not matches:
    raise FileNotFoundError(
        f"CREPE small model not found in {KERAS_MODELS}"
    )

src = matches[0]
dst = TARGET_DIR / src.name

shutil.copy(src, dst)

print(f"[SUCCESS] CREPE small model saved locally → {dst}")
