#backend/services/polyphonic/multipitch_detection.py

"""
Polyphonic Multi-Pitch Detection (Onsets & Frames)
Windows-safe | Research-grade | Verified
"""

import os
import librosa
import numpy as np
from pathlib import Path
import tempfile

from piano_transcription_inference import PianoTranscription, sample_rate

# Import your preprocessing function
from backend.services.preprocess_stereo_audio import preprocess_audio


# ============================================================
# MODEL PATH (MANUAL & SAFE)
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = BASE_DIR / "models" / "piano_transcription" / \
    "note_F1=0.9677_pedal_F1=0.9186.pth"

print("[DEBUG] Project root:", BASE_DIR)
print("[DEBUG] Model path:", MODEL_PATH)

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"❌ Onsets & Frames model not found:\n{MODEL_PATH}\n"
        f"Expected at: <project_root>/models/piano_transcription/"
    )

# ============================================================
# LOAD MODEL ONCE
# ============================================================

print("[POLYPHONIC] Loading Onsets & Frames model (manual path)...")

_transcriptor = PianoTranscription(
    device="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu",
    checkpoint_path=str(MODEL_PATH)
)

print("[POLYPHONIC] Model loaded successfully.")


# ============================================================
# PUBLIC API
# ============================================================

def detect_multipitch(audio_path: str):
    """
    Multi-pitch detection for polyphonic audio.

    Returns:
        List of note events:
        {
            pitch: MIDI int,
            onset: seconds,
            offset: seconds,
            velocity: 0-1
        }
    """

    try:
        print("\n[POLYPHONIC] ===== Multi-Pitch Detection Started =====")
        print(f"[POLYPHONIC] Original audio file: {audio_path}")

        # ------------------------------
        # Preprocess the audio first
        # ------------------------------
        # Create a temporary WAV file for the preprocessed audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            preprocessed_path = tmp_wav.name

        preprocess_audio(audio_path, preprocessed_path, sr=sample_rate)
        print(f"[POLYPHONIC] Audio preprocessed -> {preprocessed_path}")

        # Load preprocessed audio
        y, sr = librosa.load(preprocessed_path, sr=sample_rate, mono=True)
        duration = len(y) / sr
        print(f"[POLYPHONIC] Duration after preprocessing: {duration:.2f}s")

        # ------------------------------
        # Run transcription safely on Windows
        # ------------------------------
        print("[POLYPHONIC] Running Onsets & Frames inference...")

        with tempfile.NamedTemporaryFile(suffix=".midi", delete=False) as tmp_midi:
            midi_path = tmp_midi.name  # temporary MIDI path

        try:
            result = _transcriptor.transcribe(y, midi_path=midi_path)
        finally:
            # Cleanup temporary files
            if os.path.exists(midi_path):
                os.remove(midi_path)
            if os.path.exists(preprocessed_path):
                os.remove(preprocessed_path)

        # Extract note events
        notes = result.get("est_note_events", [])
        print(f"[POLYPHONIC] Notes detected: {len(notes)}")

        # Format notes
        formatted = [
            {
                "pitch": int(n["midi_note"]),
                "onset": float(n["onset_time"]),
                "offset": float(n["offset_time"]),
                "velocity": float(n["velocity"])
            }
            for n in notes
        ]

        # Verification prints
        if formatted:
            pitches = [n["pitch"] for n in formatted]
            print("[POLYPHONIC] ===== Verification =====")
            print(f"[POLYPHONIC] Pitch range: {min(pitches)} → {max(pitches)}")
            print(f"[POLYPHONIC] First note: {formatted[0]}")

        print("[POLYPHONIC] ===== Completed Successfully =====\n")
        return formatted

    except Exception as e:
        print(f"[POLYPHONIC] ❌ Error: {e}")
        return []
