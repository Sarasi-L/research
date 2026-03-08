# backend/services/polyphonic/multipitch_detection.py

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
# OFFSET POST-PROCESSING
# ============================================================

def post_process_offsets(notes, audio_path, sr=22050):
    """
    Improve offset accuracy using audio energy
    """
    print("[POLYPHONIC] Post-processing offsets for better accuracy...")
    
    try:
        y, sr = librosa.load(audio_path, sr=sr, mono=True)
        
        improved = 0
        for note in notes:
            # Look at audio around the offset
            start_sample = int(note['onset'] * sr)
            end_sample = int(note['offset'] * sr)
            
            if end_sample >= len(y) or end_sample < 0:
                continue
                
            # Check energy in last part of note
            window = int(0.05 * sr)  # 50ms window
            end_idx = min(end_sample + window, len(y))
            if end_idx <= end_sample:
                continue
                
            energy = np.abs(y[end_sample:end_idx])
            
            # If energy is still high, note might be longer
            if len(energy) > 0 and np.mean(energy) > 0.008:  # Energy threshold
                # Extend note until energy drops
                max_extend = min(int(0.3 * sr), len(y) - end_sample)  # Max 300ms extension
                for i in range(end_sample, min(end_sample + max_extend, len(y))):
                    if np.abs(y[i]) < 0.005:  # Energy dropped
                        note['offset'] = i / sr
                        improved += 1
                        break
                else:
                    # If no drop, extend to max
                    note['offset'] = (end_sample + max_extend) / sr
                    improved += 1
        
        print(f"[POLYPHONIC] Improved {improved} note offsets")
        
    except Exception as e:
        print(f"[POLYPHONIC] Offset post-processing failed: {e}")
    
    return notes


# ============================================================
# PUBLIC API
# ============================================================

def detect_multipitch(audio_path: str, post_process=True):
    """
    Multi-pitch detection for polyphonic audio.

    Args:
        audio_path: Path to audio file
        post_process: Whether to apply offset post-processing

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
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            preprocessed_path = tmp_wav.name

        preprocess_audio(audio_path, preprocessed_path, sr=sample_rate)
        print(f"[POLYPHONIC] Audio preprocessed -> {preprocessed_path}")

        # Load preprocessed audio
        y, sr = librosa.load(preprocessed_path, sr=sample_rate, mono=True)
        duration = len(y) / sr
        print(f"[POLYPHONIC] Duration after preprocessing: {duration:.2f}s")

        # ------------------------------
        # Run transcription
        # ------------------------------
        print("[POLYPHONIC] Running Onsets & Frames inference...")

        with tempfile.NamedTemporaryFile(suffix=".midi", delete=False) as tmp_midi:
            midi_path = tmp_midi.name

        try:
            result = _transcriptor.transcribe(y, midi_path=midi_path)
        finally:
            # Cleanup temporary MIDI file
            if os.path.exists(midi_path):
                os.remove(midi_path)

        # Extract note events
        notes = result.get("est_note_events", [])
        print(f"[POLYPHONIC] Raw notes detected: {len(notes)}")

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

        # Apply offset post-processing if requested
        if post_process and formatted:
            formatted = post_process_offsets(formatted, preprocessed_path)

        # Verification
        if formatted:
            pitches = [n["pitch"] for n in formatted]
            print("[POLYPHONIC] ===== Verification =====")
            print(f"[POLYPHONIC] Pitch range: {min(pitches)} → {max(pitches)}")
            print(f"[POLYPHONIC] First 5 notes: {formatted[:5]}")

        # Cleanup preprocessed file
        if os.path.exists(preprocessed_path):
            os.remove(preprocessed_path)

        print(f"[POLYPHONIC] Final notes detected: {len(formatted)}")
        print("[POLYPHONIC] ===== Completed Successfully =====\n")
        return formatted

    except Exception as e:
        print(f"[POLYPHONIC] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []