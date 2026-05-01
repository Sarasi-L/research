# backend/test_full_pipeline.py with demucs

import shutil
from pathlib import Path
import pretty_midi

# ============================================================
# IMPORT YOUR PIPELINE MODULES (MATCHING YOUR STRUCTURE)
# ============================================================

from backend.services.polyphonic.separate_demucs import separate_polyphonic
from backend.services.polyphonic.transcribe_basic_pitch import transcribe_stem
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


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_AUDIO = PROJECT_ROOT / "national-anthem3.mp3"

WORK_DIR = PROJECT_ROOT / "test_output"
STEMS_DIR = WORK_DIR / "stems"
MIDI_DIR = WORK_DIR / "midis"
FINAL_DIR = WORK_DIR / "final"

for folder in [WORK_DIR, STEMS_DIR, MIDI_DIR, FINAL_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# FULL PIPELINE
# ============================================================

def run_pipeline(audio_path: str):

    # -------------------------------------------------
    # CLEANUP: Delete all stale intermediate files
    # so the pipeline always runs completely fresh.
    # Prevents old subdivision=3 / wrong-tempo MIDIs
    # from being reused across runs.
    # -------------------------------------------------
    print("\n[CLEANUP] Clearing stale intermediate files...")

    stale_files = [
        WORK_DIR / "merged.mid",
        WORK_DIR / "cleaned.mid",
        WORK_DIR / "filtered.mid",
        WORK_DIR / "quantized.mid",
        WORK_DIR / "with_time.mid",
        WORK_DIR / "with_tempo.mid",
        WORK_DIR / "with_key.mid",
        WORK_DIR / "normalized.mid",
        FINAL_DIR / "final_score.musicxml",
    ]
    for f in stale_files:
        if f.exists():
            f.unlink()
            print(f"[CLEANUP] Deleted: {f.name}")

    if STEMS_DIR.exists():
        shutil.rmtree(STEMS_DIR)
    STEMS_DIR.mkdir(parents=True)

    if MIDI_DIR.exists():
        shutil.rmtree(MIDI_DIR)
    MIDI_DIR.mkdir(parents=True)

    print("[CLEANUP] ✓ All stale files cleared\n")

    # -------------------------------------------------

    print("\n==============================")
    print("🎵 STARTING FULL POLYPHONIC PIPELINE")
    print("==============================")

    # -------------------------------------------------
    # STEP 1 – STEM SEPARATION
    # -------------------------------------------------
    print("\n[STEP 1] Stem Separation (Demucs)")
    stems = separate_polyphonic(audio_path, STEMS_DIR)

    # -------------------------------------------------
    # STEP 2 – TRANSCRIPTION
    # -------------------------------------------------
    print("\n[STEP 2] Transcribing Stems")

    midi_files = {}

    if "vocals" in stems:
        midi_files["vocals"] = transcribe_stem(stems["vocals"], MIDI_DIR)

    if "bass" in stems:
        midi_files["bass"] = transcribe_stem(stems["bass"], MIDI_DIR)

    if "other" in stems:
        midi_files["other"] = transcribe_stem(stems["other"], MIDI_DIR)

    if "drums" in stems:
        midi_files["drums"] = transcribe_drums(stems["drums"], MIDI_DIR)

    # -------------------------------------------------
    # STEP 3 – MERGE MIDI TRACKS
    # -------------------------------------------------
    print("\n[STEP 3] Merging MIDI Tracks")
    merged_midi_path = WORK_DIR / "merged.mid"
    merged_midi = merge_midi_tracks(midi_files, merged_midi_path)

    # -------------------------------------------------
    # STEP 4 – CLEAN OVERLAPS
    # -------------------------------------------------
    print("\n[STEP 4] Cleaning Overlapping Notes")
    cleaned_midi_path = WORK_DIR / "cleaned.mid"
    clean_midi_overlaps(merged_midi, cleaned_midi_path)

    # -------------------------------------------------
    # STEP 4.5 – NOTE NOISE FILTER
    # -------------------------------------------------
    print("\n[STEP 4.5] MIDI Noise Filtering")
    filtered_midi_path = WORK_DIR / "filtered.mid"
    filter_midi_notes(
        cleaned_midi_path,
        filtered_midi_path
    )

    # -------------------------------------------------
    # STEP 5 – BEAT + TEMPO DETECTION
    # -------------------------------------------------
    print("\n[STEP 5] Beat Tracking")

    # Use drum stem for accurate beat tracking
    beat_audio = stems.get("drums", audio_path)
    tempo, beat_times = detect_beats(beat_audio)

    print(f"[STEP 5] Detected tempo: {tempo:.2f} BPM")
    print(f"[STEP 5] Beat tracking source: {beat_audio}")

    # -------------------------------------------------
    # STEP 6 – TIME SIGNATURE DETECTION
    # -------------------------------------------------
    print("\n[STEP 6] Time Signature Detection")
    numerator, denominator = detect_time_signature(
        audio_path,
        beat_times
    )
    print(f"[STEP 6] Detected time signature: {numerator}/{denominator}")

    # -------------------------------------------------
    # STEP 7 – QUANTIZATION (16th note grid)
    # FIX: pass tempo_bpm so quantizer uses a perfect
    # uniform grid instead of irregular librosa beats.
    # -------------------------------------------------
    print("\n[STEP 7] Quantization")
    quantized_midi_path = WORK_DIR / "quantized.mid"
    quantize_to_grid(
        filtered_midi_path,
        beat_times,
        quantized_midi_path,
        subdivision=4,
        tempo_bpm=tempo         # ← THIS IS THE KEY FIX
    )

    # -------------------------------------------------
    # STEP 8 – KEY DETECTION
    # -------------------------------------------------
    print("\n[STEP 8] Key Detection")
    key, mode = detect_key(quantized_midi_path)

    # -------------------------------------------------
    # STEP 9 – APPLY TIME SIGNATURE
    # -------------------------------------------------
    print("\n[STEP 9] Applying Time Signature")
    ts_applied_path = WORK_DIR / "with_time.mid"
    apply_time_signature(
        quantized_midi_path,
        numerator,
        denominator,
        ts_applied_path
    )

    # -------------------------------------------------
    # STEP 9.5 – APPLY TEMPO
    # Explicitly passing tempo prevents music21 from
    # defaulting to 120 BPM during XML export.
    # -------------------------------------------------
    print("\n[STEP 9.5] Applying Tempo")
    tempo_applied_path = WORK_DIR / "with_tempo.mid"
    apply_tempo(
        ts_applied_path,
        tempo,
        tempo_applied_path
    )
    print(f"[STEP 9.5] Tempo applied: {tempo:.2f} BPM")

    # -------------------------------------------------
    # STEP 10 – APPLY KEY SIGNATURE
    # -------------------------------------------------
    print("\n[STEP 10] Applying Key Signature")
    key_applied_path = WORK_DIR / "with_key.mid"
    apply_key_to_midi(
        tempo_applied_path,
        key,
        mode,
        key_applied_path
    )

    # -------------------------------------------------
    # STEP 10.5 – NOTE DURATION NORMALIZATION
    # tempo_bpm passed so grid uses real beat duration,
    # not hardcoded 120 BPM equivalent values.
    # -------------------------------------------------
    print("\n[STEP 10.5] Normalizing Note Durations")
    normalized_midi_path = WORK_DIR / "normalized.mid"
    normalize_note_durations(
        key_applied_path,
        normalized_midi_path,
        tempo_bpm=tempo
    )

    
    # Load the correct file
    m = pretty_midi.PrettyMIDI(normalized_midi_path)
    print("MIDI duration:", m.get_end_time())

    # -------------------------------------------------
    # STEP 11 – EXPORT MUSICXML
    # -------------------------------------------------
    print("\n[STEP 11] Exporting MusicXML")
    final_xml = FINAL_DIR / "final_score.musicxml"
    
    midi_to_musicxml(
        normalized_midi_path,
        final_xml,
        tempo
    )

    print("\n==============================")
    print("✅ PIPELINE COMPLETE")
    print(f"🎼 Final XML: {final_xml}")
    print(f"🎵 Tempo: {tempo:.2f} BPM")
    print(f"🎼 Key: {key} {mode}")
    print(f"⏱  Time Signature: {numerator}/{denominator}")
    print("==============================\n")

    return final_xml


# ============================================================
# RUN TEST
# ============================================================

if __name__ == "__main__":

    if not INPUT_AUDIO.exists():
        print(f"❌ Test audio not found: {INPUT_AUDIO}")
    else:
        run_pipeline(str(INPUT_AUDIO))