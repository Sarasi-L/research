# ==========================================================
# Mono / Polyphonic Classification – CRNN Inference (PyTorch)
# ==========================================================

import torch
import torch.nn as nn
import numpy as np
import librosa
from pathlib import Path

# =========================
# CONFIG
# =========================
AUDIO_PATH = "(02) dont kill the whale-1.wav"
MODEL_PATH = "models/MonoPoly/mono_poly_crnn.pth"

SR = 16000
WINDOW_SEC = 3.0
HOP_SEC = 1.5

# 🔥 MUST MATCH TRAINING FEATURE SHAPE
N_MELS = 128
N_FFT = 1024
HOP_LENGTH = 512      # <-- MATCH TRAINING
EXPECTED_FRAMES = 128

device = "cuda" if torch.cuda.is_available() else "cpu"

# =========================
# MODEL DEFINITION
# =========================
class CRNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d((2, 2)),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d((2, 2))
        )
        self.gru = nn.GRU(input_size=64*32, hidden_size=128, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(256, 2)

    def forward(self, x):
        x = self.cnn(x)               # (B, C, F, T)
        x = x.permute(0, 3, 1, 2)     # (B, T, C, F)
        x = x.flatten(2)              # (B, T, C*F)
        x, _ = self.gru(x)
        x = x.mean(dim=1)
        return self.fc(x)

# =========================
# LOAD MODEL
# =========================
if not Path(MODEL_PATH).exists():
    raise FileNotFoundError(f"❌ Model not found: {MODEL_PATH}")

model = CRNN().to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()
print("✅ CRNN model loaded")

# =========================
# AUDIO UTILITIES
# =========================
def audio_to_chunks(y, window, hop):
    return [y[i:i+window] for i in range(0, len(y)-window+1, hop)]

def preprocess_chunk(y):
    """ MUST MATCH TRAINING PREPROCESSING """
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SR,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        power=2.0
    )
    mel = librosa.power_to_db(mel, ref=np.max)
    
    # ✅ Normalize like training
    mel = (mel - np.mean(mel)) / (np.std(mel) + 1e-6)

    # Pad / trim
    if mel.shape[1] < EXPECTED_FRAMES:
        mel = np.pad(mel, ((0,0),(0, EXPECTED_FRAMES - mel.shape[1])), mode='constant')
    else:
        mel = mel[:, :EXPECTED_FRAMES]

    mel = torch.tensor(mel, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
    return mel.to(device)

# =========================
# RUN INFERENCE
# =========================
y, _ = librosa.load(AUDIO_PATH, sr=SR, mono=True)
win = int(SR*WINDOW_SEC)
hop = int(SR*HOP_SEC)
chunks = audio_to_chunks(y, win, hop)
if len(chunks) == 0:
    raise ValueError("❌ Audio shorter than 3 seconds")

probs = []
with torch.no_grad():
    for chunk in chunks:
        X = preprocess_chunk(chunk)
        logits = model(X)
        prob_poly = torch.softmax(logits, dim=1)[0,1].item()
        probs.append(prob_poly)
probs = np.array(probs)

# =========================
# AGGREGATION
# =========================
mean_prob = probs.mean()
max_prob = probs.max()
poly_ratio = np.mean(probs > 0.5)

# Option 1: using poly_ratio threshold (original)
# label = "POLYPHONIC 🎼" if poly_ratio >= 0.4 else "MONOPHONIC 🎵"

# Option 2: using mean probability (safer for real audio)
label = "POLYPHONIC 🎼" if mean_prob >= 0.4 else "MONOPHONIC 🎵"

# =========================
# OUTPUT
# =========================
print("\n================ RESULT ================")
print(f"🎧 Audio file        : {AUDIO_PATH}")
print(f"⏱ Duration          : {len(y)/SR:.1f} seconds")
print(f"🧩 Chunks analysed   : {len(probs)}")
print(f"📊 Mean poly prob    : {mean_prob:.4f}")
print(f"📈 Max poly prob     : {max_prob:.4f}")
print(f"🎼 Poly chunk ratio  : {poly_ratio:.2f}")
print(f"✅ FINAL PREDICTION  : {label}")
print("========================================")
