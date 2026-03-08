
# #backend/services/polyphonic/voice_separation.py
# """
# Polyphonic Voice Separation
# Windows-safe | Research-grade | Verified
# """

# import os
# import librosa
# import numpy as np
# import soundfile as sf
# from pathlib import Path
# import tempfile

# # ============================================================
# # Helper function: simple separation by harmonic/percussive
# # ============================================================

# def separate_voices(audio_path: str, output_dir: str = None):
#     """
#     Separate a polyphonic audio into voices (harmonic and percussive as example)

#     Args:
#         audio_path: Path to input audio
#         output_dir: Optional directory to save separated voices

#     Returns:
#         List of dicts per voice:
#         [
#             {
#                 "voice_name": str,
#                 "audio": np.ndarray,
#                 "sr": int,
#                 "file_path": str
#             },
#             ...
#         ]
#     """

#     print("\n[VOICE SEP] ===== Voice Separation Started =====")
#     print(f"[VOICE SEP] Original audio: {audio_path}")

#     y, sr = librosa.load(audio_path, sr=None, mono=True)
#     duration = len(y)/sr
#     print(f"[VOICE SEP] Audio duration: {duration:.2f}s, Sample rate: {sr}")

#     # Create output directory if not provided
#     if output_dir is None:
#         output_dir = tempfile.mkdtemp(prefix="voices_")
#     else:
#         os.makedirs(output_dir, exist_ok=True)

#     # ------------------------
#     # Harmonic/Percussive separation
#     # ------------------------
#     print("[VOICE SEP] Running Harmonic/Percussive Separation (HPS)...")
#     harmonic, percussive = librosa.effects.hpss(y)

#     voices = [
#         {"voice_name": "harmonic", "audio": harmonic, "sr": sr},
#         {"voice_name": "percussive", "audio": percussive, "sr": sr}
#     ]

#     # Save each separated voice as WAV
#     for v in voices:
#         file_path = os.path.join(output_dir, f"{v['voice_name']}.wav")
#         sf.write(file_path, v["audio"], sr)
#         v["file_path"] = file_path
#         print(f"[VOICE SEP] {v['voice_name']} voice saved -> {file_path}")
#         print(f"[VOICE SEP] {v['voice_name']} duration: {len(v['audio'])/sr:.2f}s")

#     print("[VOICE SEP] ===== Voice Separation Completed =====\n")
#     return voices
