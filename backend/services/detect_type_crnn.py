# backend/services/detect_type_crnn.py
"""
CRNN-based Monophonic vs Polyphonic Audio Classifier
Replaces rule-based + CREPE detector
Matches training & inference specification exactly
"""

import torch
import torch.nn as nn
import librosa
import numpy as np
from pathlib import Path

# ============================================================
# CONFIG (MATCH TRAINING)
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]  
MODEL_PATH = BASE_DIR / "models" / "MonoPoly" / "mono_poly_crnn.pth"

SR = 16000
MAX_DURATION_SEC = 60.0   # ✅ process up to 60 seconds

WINDOW_SEC = 3.0
HOP_SEC = 1.5

N_MELS = 128
N_FFT = 1024
HOP_LENGTH = 512
EXPECTED_FRAMES = 128

POLY_THRESHOLD = 0.4

device = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================================
# MODEL DEFINITION (EXACT MATCH)
# ============================================================

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

        self.gru = nn.GRU(
            input_size=64 * 32,
            hidden_size=128,
            batch_first=True,
            bidirectional=True
        )

        self.fc = nn.Linear(256, 2)

    def forward(self, x):
        x = self.cnn(x)               # (B, C, F, T)
        x = x.permute(0, 3, 1, 2)     # (B, T, C, F)
        x = x.flatten(2)              # (B, T, C*F)
        x, _ = self.gru(x)
        x = x.mean(dim=1)
        return self.fc(x)


# ============================================================
# LOAD MODEL (ONCE)
# ============================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"❌ CRNN model not found: {MODEL_PATH}")

_model = CRNN().to(device)
_model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
_model.eval()


# ============================================================
# PUBLIC API
# ============================================================

def detect_type(audio_path: str) -> tuple:
    """
    Detect if audio is monophonic or polyphonic using CRNN

    Returns:
        (type_string, confidence)
    """

    try:
        y, _ = librosa.load(
            audio_path,
            sr=SR,
            mono=True,
            duration=MAX_DURATION_SEC
        )

        chunks = _audio_to_chunks(y)

        if len(chunks) == 0:
            return "polyphonic", 0.6

        probs = []

        with torch.no_grad():
            for chunk in chunks:
                X = _preprocess_chunk(chunk)
                logits = _model(X)
                prob_poly = torch.softmax(logits, dim=1)[0, 1].item()
                probs.append(prob_poly)

        probs = np.array(probs)

        mean_prob = float(probs.mean())
        poly_ratio = float(np.mean(probs > 0.5))

        # ✅ Same decision logic as your test script
        label = "polyphonic" if mean_prob >= POLY_THRESHOLD else "monophonic"
        confidence = mean_prob if label == "polyphonic" else 1.0 - mean_prob

        return label, round(confidence, 3)

    except Exception as e:
        print(f"[WARNING] CRNN detect_type failed: {e}")
        return "polyphonic", 0.6


# ============================================================
# UTILITIES
# ============================================================

def _audio_to_chunks(y):
    win = int(SR * WINDOW_SEC)
    hop = int(SR * HOP_SEC)
    return [
        y[i:i + win]
        for i in range(0, len(y) - win + 1, hop)
    ]


def _preprocess_chunk(y):
    """
    MUST MATCH TRAINING PREPROCESSING
    """

    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SR,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        power=2.0
    )

    mel = librosa.power_to_db(mel, ref=np.max)

    # ✅ normalization (same as training)
    mel = (mel - mel.mean()) / (mel.std() + 1e-6)

    # Pad / trim to fixed time dimension
    if mel.shape[1] < EXPECTED_FRAMES:
        mel = np.pad(
            mel,
            ((0, 0), (0, EXPECTED_FRAMES - mel.shape[1])),
            mode="constant"
        )
    else:
        mel = mel[:, :EXPECTED_FRAMES]

    mel = torch.tensor(mel, dtype=torch.float32)
    mel = mel.unsqueeze(0).unsqueeze(0)  # (1, 1, F, T)

    return mel.to(device)
