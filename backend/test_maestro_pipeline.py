# backend/test_maestro_pipeline.py piano only

from pathlib import Path
import shutil
import csv
import pretty_midi
import tempfile

from backend.services.polyphonic.multipitch_detection import detect_multipitch
from backend.services.polyphonic.quantize_midi import quantize_to_grid
from backend.services.polyphonic.beat_tracking import detect_beats
from backend.services.polyphonic.time_signature import detect_time_signature
from backend.services.polyphonic.key_detection import detect_key
from backend.services.polyphonic.apply_time_signature import apply_time_signature
from backend.services.polyphonic.apply_key_signature import apply_key_to_midi
from backend.services.polyphonic.apply_tempo import apply_tempo
from backend.services.polyphonic.note_duration_normalizer import normalize_note_durations
from backend.services.polyphonic.export_musicxml import midi_to_musicxml

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
MAESTRO_DIR = PROJECT_ROOT / "notation_sheet_validation" / "maestro"
EVAL_OUTPUT_DIR = PROJECT_ROOT / "notation_sheet_validation" / "eval_outputs"
MAX_SONGS = None


# ============================================================
# ONSETS & FRAMES TRANSCRIPTION
# ============================================================

def transcribe_with_onsets_frames(audio_path: str, output_dir: Path):
    """
    Use Onsets & Frames for better recall than Basic Pitch
    """
    print("\n[TRANSCRIBE] Using Onsets & Frames...")
    
    # Detect notes
    notes = detect_multipitch(str(audio_path), post_process=True)
    
    if not notes or len(notes) < 10:
        print("[TRANSCRIBE] Too few notes detected, falling back to Basic Pitch")
        from backend.services.polyphonic.transcribe_basic_pitch import transcribe_stem
        midi_path = transcribe_stem(str(audio_path), str(output_dir))
        return midi_path
    
    # Create MIDI from notes
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    
    for n in notes:
        # Convert velocity from 0-1 to 0-127
        velocity = int(np.clip(n['velocity'] * 127, 30, 110))
        
        note = pretty_midi.Note(
            velocity=velocity,
            pitch=n['pitch'],
            start=n['onset'],
            end=n['offset']
        )
        instrument.notes.append(note)
    
    midi.instruments.append(instrument)
    
    # Save
    # Save
    output_dir.mkdir(parents=True, exist_ok=True)

    short_name = Path(audio_path).stem[:40]
    output_path = output_dir / f"{short_name}_onsets.mid"

    midi.write(str(output_path))
   
    
    print(f"[TRANSCRIBE] ✓ Saved {len(notes)} notes to {output_path}")
    return str(output_path)


# ============================================================
# PAIR FINDER
# ============================================================

def find_pairs(maestro_dir: Path):
    """Scan folder for (audio, gt_midi) pairs"""
    pairs = []
    audio_files = sorted([
        f for f in maestro_dir.iterdir()
        if f.suffix.lower() in {".mp3", ".wav", ".flac"}
    ])

    for audio in audio_files:
        stem = audio.stem
        candidates = [
            f for f in maestro_dir.iterdir()
            if f.stem == stem and f.suffix.lower() in {".mid", ".midi"}
        ]

        if not candidates:
            print(f"[SKIP] No matching MIDI for: {audio.name}")
            continue

        gt_midi = max(candidates, key=lambda f: f.stat().st_size)
        pairs.append((audio, gt_midi))

    return pairs


# ============================================================
# SINGLE SONG PIPELINE
# ============================================================

def run_pipeline_for_song(audio_path: Path, gt_midi_path: Path,
                           song_output_dir: Path):
    """Run full transcription pipeline for one audio file"""
    
    # Fresh output directory
    if song_output_dir.exists():
        shutil.rmtree(song_output_dir)
    song_output_dir.mkdir(parents=True)

    print(f"\n{'='*55}")
    print(f"Song : {audio_path.name}")
    print(f"GT   : {gt_midi_path.name} ({gt_midi_path.stat().st_size // 1024} KB)")
    print(f"Out  : {song_output_dir}")
    print(f"{'='*55}")

    # --------------------------------------------------
    # STEP 1 — TRANSCRIPTION (ONSETS & FRAMES)
    # --------------------------------------------------
    print("\n[STEP 1] Transcription (Onsets & Frames)")
    raw_mid_path = transcribe_with_onsets_frames(str(audio_path), song_output_dir)
    raw_mid = Path(raw_mid_path)
    print(f"  Raw MIDI: {raw_mid.name}")

    # --------------------------------------------------
    # STEP 2 — BEAT TRACKING
    # --------------------------------------------------
    print("\n[STEP 2] Beat Tracking")
    tempo, beat_times = detect_beats(str(audio_path))
    print(f"  Tempo: {tempo:.2f} BPM  |  Beats: {len(beat_times)}")

    # --------------------------------------------------
    # STEP 3 — TIME SIGNATURE
    # --------------------------------------------------
    print("\n[STEP 3] Time Signature Detection")
    numerator, denominator = detect_time_signature(str(audio_path), beat_times)
    print(f"  Time Sig: {numerator}/{denominator}")

    # --------------------------------------------------
    # STEP 4 — QUANTIZATION
    # --------------------------------------------------
    print("\n[STEP 4] Quantization")
    quantized_mid = song_output_dir / "quantized.mid"
    quantize_to_grid(
        str(raw_mid),
        beat_times,
        str(quantized_mid),
        subdivision=4,
        tempo_bpm=tempo
    )

    # --------------------------------------------------
    # STEP 5 — APPLY TIME SIGNATURE
    # --------------------------------------------------
    ts_mid = song_output_dir / "with_time.mid"
    apply_time_signature(str(quantized_mid), numerator, denominator, str(ts_mid))

    # --------------------------------------------------
    # STEP 6 — APPLY TEMPO
    # --------------------------------------------------
    tempo_mid = song_output_dir / "with_tempo.mid"
    apply_tempo(str(ts_mid), tempo, str(tempo_mid))

    # --------------------------------------------------
    # STEP 7 — KEY DETECTION
    # --------------------------------------------------
    print("\n[STEP 7] Key Detection")
    key, mode = detect_key(str(tempo_mid))
    print(f"  Key: {key} {mode}")

    key_mid = song_output_dir / "with_key.mid"
    apply_key_to_midi(str(tempo_mid), key, mode, str(key_mid))

    # --------------------------------------------------
    # STEP 8 — NORMALIZE DURATIONS
    # --------------------------------------------------
    print("\n[STEP 8] Normalize Durations")
    normalized_mid = song_output_dir / "normalized.mid"
    normalize_note_durations(str(key_mid), str(normalized_mid), tempo_bpm=tempo)

    # --------------------------------------------------
    # STEP 9 — EXPORT MUSICXML
    # --------------------------------------------------
    print("\n[STEP 9] Export MusicXML")
    predicted_xml = song_output_dir / "predicted.musicxml"
    midi_to_musicxml(str(normalized_mid), str(predicted_xml), tempo)

    # Copy GT MIDI for evaluation
    gt_copy = song_output_dir / "ground_truth.mid"
    shutil.copy2(gt_midi_path, gt_copy)

    print(f"\n✅ {audio_path.name} complete")
    return normalized_mid, predicted_xml


# ============================================================
# BATCH RUNNER
# ============================================================

def run_batch():
    EVAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pairs = find_pairs(MAESTRO_DIR)

    if not pairs:
        print(f"\n❌ No audio+MIDI pairs found in:\n   {MAESTRO_DIR}")
        return

    if MAX_SONGS:
        pairs = pairs[:MAX_SONGS]

    print(f"\nFound {len(pairs)} pair(s). Processing up to {MAX_SONGS}.\n")

    # Manifest CSV
    manifest_path = EVAL_OUTPUT_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "song_name", "audio_path", "gt_midi_path",
            "predicted_midi_path", "predicted_xml_path",
            "gt_midi_copy_path", "status", "error"
        ])

    success = 0
    failed = 0

    for idx, (audio_path, gt_midi_path) in enumerate(pairs, 1):
        song_name = audio_path.stem
        song_out = EVAL_OUTPUT_DIR / song_name

        print(f"\n[{idx}/{len(pairs)}]", end="")

        try:
            pred_mid, pred_xml = run_pipeline_for_song(
                audio_path, gt_midi_path, song_out)

            gt_copy = song_out / "ground_truth.mid"

            with open(manifest_path, "a", newline="") as f:
                csv.writer(f).writerow([
                    song_name, audio_path, gt_midi_path,
                    str(pred_mid), str(pred_xml),
                    str(gt_copy), "success", ""
                ])
            success += 1

        except Exception as e:
            print(f"\n❌ FAILED: {audio_path.name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            with open(manifest_path, "a", newline="") as f:
                csv.writer(f).writerow([
                    song_name, audio_path, gt_midi_path,
                    "", "", "", "failed", str(e)
                ])
            failed += 1

    print(f"\n{'='*55}")
    print(f"BATCH COMPLETE")
    print(f"  Successful : {success}")
    print(f"  Failed     : {failed}")
    print(f"  Manifest   : {manifest_path}")
    print(f"{'='*55}\n")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Import numpy here to avoid circular imports
    import numpy as np
    run_batch()