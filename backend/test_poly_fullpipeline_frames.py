# backend/test_full_pipeline.py
# FULL POLYPHONIC PIPELINE USING DEMUCS + ONSETS & FRAMES

import shutil
from pathlib import Path
import pretty_midi
import numpy as np

# ============================================================
# IMPORT PIPELINE MODULES
# ============================================================

from backend.services.polyphonic.separate_demucs import separate_polyphonic
from backend.services.polyphonic.transcribe_drums import transcribe_drums
from backend.services.polyphonic.merge_midi import merge_midi_tracks
from backend.services.polyphonic.quantize_midi import quantize_to_grid
from backend.services.polyphonic.beat_tracking import detect_beats
from backend.services.polyphonic.time_signature import detect_time_signature
from backend.services.polyphonic.key_detection import detect_key
from backend.services.polyphonic.apply_time_signature import apply_time_signature
from backend.services.polyphonic.apply_key_signature import apply_key_to_midi
from backend.services.polyphonic.export_musicxml import midi_to_musicxml
from backend.services.polyphonic.score_cleaner import clean_midi_overlaps
from backend.services.polyphonic.apply_tempo import apply_tempo
from backend.services.polyphonic.midi_note_filter import filter_midi_notes
from backend.services.polyphonic.note_duration_normalizer import normalize_note_durations
from backend.services.polyphonic.multipitch_detection import detect_multipitch


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_AUDIO = PROJECT_ROOT / "national-anthem.mp3"

WORK_DIR = PROJECT_ROOT / "test_output"
STEMS_DIR = WORK_DIR / "stems"
MIDI_DIR = WORK_DIR / "midis"
FINAL_DIR = WORK_DIR / "final"

for folder in [WORK_DIR, STEMS_DIR, MIDI_DIR, FINAL_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# ONSETS & FRAMES TRANSCRIPTION FUNCTION
# ============================================================

def transcribe_with_onsets_frames(audio_path: str, output_dir: Path):

    print(f"[TRANSCRIBE] Onsets & Frames: {Path(audio_path).name}")

    notes = detect_multipitch(audio_path, post_process=True)

    if not notes:
        print("[TRANSCRIBE] ⚠ No notes detected")
        return None

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    for n in notes:

        velocity = int(np.clip(n['velocity'] * 127, 30, 110))

        note = pretty_midi.Note(
            velocity=velocity,
            pitch=n['pitch'],
            start=n['onset'],
            end=n['offset']
        )

        instrument.notes.append(note)

    midi.instruments.append(instrument)

    output_dir.mkdir(parents=True, exist_ok=True)

    name = Path(audio_path).stem
    output_path = output_dir / f"{name}_onsets.mid"

    midi.write(str(output_path))

    print(f"[TRANSCRIBE] ✓ {len(notes)} notes saved")

    return str(output_path)


# ============================================================
# FULL PIPELINE
# ============================================================

def run_pipeline(audio_path: str):

    print("\n[CLEANUP] Clearing old files...")

    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)

    WORK_DIR.mkdir()
    STEMS_DIR.mkdir()
    MIDI_DIR.mkdir()
    FINAL_DIR.mkdir()

    print("[CLEANUP] ✓ Fresh workspace ready")

    print("\n==============================")
    print("🎵 STARTING FULL POLYPHONIC PIPELINE")
    print("==============================")

    # -------------------------------------------------
    # STEP 1 – STEM SEPARATION
    # -------------------------------------------------

    print("\n[STEP 1] Demucs Stem Separation")

    stems = separate_polyphonic(audio_path, STEMS_DIR)

    # -------------------------------------------------
    # STEP 2 – TRANSCRIBE STEMS
    # -------------------------------------------------

    print("\n[STEP 2] Transcribing Stems")

    midi_files = {}

    if "vocals" in stems:
        midi_files["vocals"] = transcribe_with_onsets_frames(
            stems["vocals"], MIDI_DIR)

    if "bass" in stems:
        midi_files["bass"] = transcribe_with_onsets_frames(
            stems["bass"], MIDI_DIR)

    if "other" in stems:
        midi_files["other"] = transcribe_with_onsets_frames(
            stems["other"], MIDI_DIR)

    if "drums" in stems:
        midi_files["drums"] = transcribe_drums(
            stems["drums"], MIDI_DIR)

    # -------------------------------------------------
    # STEP 3 – MERGE MIDI TRACKS
    # -------------------------------------------------

    print("\n[STEP 3] Merging MIDI Tracks")

    merged_midi_path = WORK_DIR / "merged.mid"

    merged_midi = merge_midi_tracks(
        midi_files,
        merged_midi_path
    )

    # -------------------------------------------------
    # STEP 4 – CLEAN OVERLAPS
    # -------------------------------------------------

    print("\n[STEP 4] Cleaning MIDI Overlaps")

    cleaned_midi_path = WORK_DIR / "cleaned.mid"

    clean_midi_overlaps(
        merged_midi,
        cleaned_midi_path
    )

    # -------------------------------------------------
    # STEP 4.5 – NOTE FILTER
    # -------------------------------------------------

    print("\n[STEP 4.5] MIDI Noise Filtering")

    filtered_midi_path = WORK_DIR / "filtered.mid"

    filter_midi_notes(
        cleaned_midi_path,
        filtered_midi_path
    )

    # -------------------------------------------------
    # STEP 5 – BEAT TRACKING
    # -------------------------------------------------

    print("\n[STEP 5] Beat Tracking")

    beat_audio = stems.get("drums", audio_path)

    tempo, beat_times = detect_beats(beat_audio)

    print(f"Tempo: {tempo:.2f} BPM")

    # -------------------------------------------------
    # STEP 6 – TIME SIGNATURE
    # -------------------------------------------------

    print("\n[STEP 6] Time Signature Detection")

    numerator, denominator = detect_time_signature(
        audio_path,
        beat_times
    )

    print(f"Time Signature: {numerator}/{denominator}")

    # -------------------------------------------------
    # STEP 7 – QUANTIZATION
    # -------------------------------------------------

    print("\n[STEP 7] Quantization")

    quantized_midi_path = WORK_DIR / "quantized.mid"

    quantize_to_grid(
        filtered_midi_path,
        beat_times,
        quantized_midi_path,
        subdivision=4,
        tempo_bpm=tempo
    )

    # -------------------------------------------------
    # STEP 8 – KEY DETECTION
    # -------------------------------------------------

    print("\n[STEP 8] Key Detection")

    key, mode = detect_key(quantized_midi_path)

    print(f"Key: {key} {mode}")

    # -------------------------------------------------
    # STEP 9 – APPLY TIME SIGNATURE
    # -------------------------------------------------

    print("\n[STEP 9] Apply Time Signature")

    ts_midi = WORK_DIR / "with_time.mid"

    apply_time_signature(
        quantized_midi_path,
        numerator,
        denominator,
        ts_midi
    )

    # -------------------------------------------------
    # STEP 9.5 – APPLY TEMPO
    # -------------------------------------------------

    print("\n[STEP 9.5] Apply Tempo")

    tempo_midi = WORK_DIR / "with_tempo.mid"

    apply_tempo(
        ts_midi,
        tempo,
        tempo_midi
    )

    # -------------------------------------------------
    # STEP 10 – APPLY KEY
    # -------------------------------------------------

    print("\n[STEP 10] Apply Key Signature")

    key_midi = WORK_DIR / "with_key.mid"

    apply_key_to_midi(
        tempo_midi,
        key,
        mode,
        key_midi
    )

    # -------------------------------------------------
    # STEP 10.5 – NORMALIZE DURATIONS
    # -------------------------------------------------

    print("\n[STEP 10.5] Normalize Note Durations")

    normalized_midi = WORK_DIR / "normalized.mid"

    normalize_note_durations(
        key_midi,
        normalized_midi,
        tempo_bpm=tempo
    )

    m = pretty_midi.PrettyMIDI(normalized_midi)

    print("MIDI duration:", m.get_end_time())

    # -------------------------------------------------
    # STEP 11 – EXPORT MUSICXML
    # -------------------------------------------------

    print("\n[STEP 11] Export MusicXML")

    final_xml = FINAL_DIR / "final_score.musicxml"

    midi_to_musicxml(
        normalized_midi,
        final_xml,
        tempo
    )

    print("\n==============================")
    print("✅ PIPELINE COMPLETE")
    print("==============================")

    print("XML:", final_xml)
    print("Tempo:", tempo)
    print("Key:", key, mode)
    print("Time Signature:", numerator, denominator)

    return final_xml


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    if not INPUT_AUDIO.exists():
        print("❌ Input audio not found:", INPUT_AUDIO)

    else:
        run_pipeline(str(INPUT_AUDIO))