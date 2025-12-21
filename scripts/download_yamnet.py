# save_yamnet.py
from pathlib import Path
import tensorflow_hub as hub
import tensorflow as tf

# Project root (adjust if needed)
base_dir = Path(__file__).resolve().parents[1]
models_dir = base_dir / "models" / "yamnet"
models_dir.mkdir(parents=True, exist_ok=True)

# Load YAMNet from TF Hub
yamnet_model_handle = "https://tfhub.dev/google/yamnet/1"
yamnet_model = hub.load(yamnet_model_handle)

# Save locally
tf.saved_model.save(yamnet_model, str(models_dir))
print(f"YAMNet saved locally at: {models_dir}")
