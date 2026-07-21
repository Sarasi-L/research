from demucs.pretrained import get_model
import torch
import os

SAVE_DIR = "models/htdemucs"
os.makedirs(SAVE_DIR, exist_ok=True)

model = get_model("htdemucs")

torch.save(model.state_dict(), f"{SAVE_DIR}/htdemucs.th")
print("HTDemucs model downloaded and saved successfully!")
