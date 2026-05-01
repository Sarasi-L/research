# backend/services/polyphonic/run_polyphonic_pipeline.py

from pathlib import Path
import shutil
import pretty_midi

from services.polyphonic.separate_demucs import separate_polyphonic
from services.polyphonic.transcribe_basic_pitch import transcribe_stem
from services.polyphonic.transcribe_drums import transcribe_drums
from services.polyphonic.merge_midi import merge_midi_tracks
from services.polyphonic.quantize_midi import quantize_to_grid
from services.polyphonic.beat_tracking import detect_beats
from services.polyphonic.time_signature import detect_time_signature
from services.polyphonic.key_detection import detect_key
from services.polyphonic.apply_time_signature import apply_time_signature
from services.polyphonic.apply_key_signature import apply_key_to_midi
from services.polyphonic.apply_tempo import apply_tempo
from services.polyphonic.export_musicxml import midi_to_musicxml
from services.polyphonic.score_cleaner import clean_midi_overlaps
from services.polyphonic.midi_note_filter import filter_midi_notes
from services.polyphonic.note_duration_normalizer import normalize_note_durations

from services.cross_notation.midi_to_sargam import midi_to_sargam, sargam_string


def run_polyphonic_pipeline(audio_path: str, output_dir: str):

    output_dir = Path(output_dir)
    work_dir = output_dir / "poly_work"
    stems_dir = work_dir / "stems"
    midi_dir = work_dir / "midis"

    for d in [work_dir, stems_dir, midi_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print("\n===== MULTI-INSTRUMENT PIPELINE START =====")

    # -------------------------------------------------
    # STEP 1 — DEMUCS SEPARATION
    # -------------------------------------------------

    stems = separate_polyphonic(audio_path, stems_dir)

    # -------------------------------------------------
    # STEP 2 — TRANSCRIBE STEMS
    # -------------------------------------------------

    midi_files = {}

    if "vocals" in stems:
        midi_files["vocals"] = transcribe_stem(stems["vocals"], midi_dir)

    if "bass" in stems:
        midi_files["bass"] = transcribe_stem(stems["bass"], midi_dir)

    if "other" in stems:
        midi_files["other"] = transcribe_stem(stems["other"], midi_dir)

    if "drums" in stems:
        midi_files["drums"] = transcribe_drums(stems["drums"], midi_dir)

    # -------------------------------------------------
    # STEP 3 — MERGE MIDI
    # -------------------------------------------------

    merged_midi = work_dir / "merged.mid"
    merge_midi_tracks(midi_files, merged_midi)

    # -------------------------------------------------
    # STEP 4 — CLEAN MIDI
    # -------------------------------------------------

    cleaned_midi = work_dir / "cleaned.mid"
    clean_midi_overlaps(merged_midi, cleaned_midi)

    # -------------------------------------------------
    # STEP 5 — FILTER MIDI NOISE
    # -------------------------------------------------

    filtered_midi = work_dir / "filtered.mid"
    filter_midi_notes(cleaned_midi, filtered_midi)

    # -------------------------------------------------
    # STEP 6 — TEMPO + BEATS
    # -------------------------------------------------

    beat_audio = stems.get("drums", audio_path)
    tempo, beat_times = detect_beats(beat_audio)

    # -------------------------------------------------
    # STEP 7 — TIME SIGNATURE
    # -------------------------------------------------

    numerator, denominator = detect_time_signature(audio_path, beat_times)

    # -------------------------------------------------
    # STEP 8 — QUANTIZE
    # -------------------------------------------------

    quantized_midi = work_dir / "quantized.mid"

    quantize_to_grid(
        filtered_midi,
        beat_times,
        quantized_midi,
        subdivision=4,
        tempo_bpm=tempo
    )

    # -------------------------------------------------
    # STEP 9 — APPLY TIME SIGNATURE
    # -------------------------------------------------

    ts_mid = work_dir / "with_time.mid"

    apply_time_signature(
        quantized_midi,
        numerator,
        denominator,
        ts_mid
    )

    # -------------------------------------------------
    # STEP 10 — APPLY TEMPO
    # -------------------------------------------------

    tempo_mid = work_dir / "with_tempo.mid"

    apply_tempo(
        ts_mid,
        tempo,
        tempo_mid
    )

    # -------------------------------------------------
    # STEP 11 — KEY DETECTION
    # -------------------------------------------------

    key, mode = detect_key(tempo_mid)

    key_mid = work_dir / "with_key.mid"

    apply_key_to_midi(
        tempo_mid,
        key,
        mode,
        key_mid
    )

    # -------------------------------------------------
    # STEP 12 — NORMALIZE NOTE DURATIONS
    # -------------------------------------------------

    normalized_mid = work_dir / "normalized.mid"

    normalize_note_durations(
        key_mid,
        normalized_mid,
        tempo_bpm=tempo
    )

    # -------------------------------------------------
    # COPY FINAL MIDI TO OUTPUT DIRECTORY
    # -------------------------------------------------

    final_midi_path = output_dir / "final_polyphonic.mid"
    shutil.copy(normalized_mid, final_midi_path)

    # -----------------------------------------
    # STEP 13 — GENERATE SARGAM
    # -----------------------------------------

    sargam_notes = midi_to_sargam(str(normalized_mid), tonic=key, beats_per_measure=numerator)
    sargam_text = sargam_string(sargam_notes, beats_per_measure=numerator, bpm=tempo)

    # -------------------------------------------------
    # STEP 13 — EXPORT MUSICXML
    # -------------------------------------------------

    xml_path = output_dir / "final_polyphonic.musicxml"

    midi_to_musicxml(
        normalized_mid,
        xml_path,
        tempo
    )

    print("===== MULTI-INSTRUMENT PIPELINE COMPLETE =====")

    return {
        "xml": str(xml_path),
        "midi": str(final_midi_path),
        "sargam": sargam_text
    }