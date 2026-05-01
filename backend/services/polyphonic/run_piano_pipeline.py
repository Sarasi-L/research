# backend/services/polyphonic/run_piano_pipeline.py

from pathlib import Path
import pretty_midi

from services.polyphonic.quantize_midi import quantize_to_grid
from services.polyphonic.beat_tracking import detect_beats
from services.polyphonic.time_signature import detect_time_signature
from services.polyphonic.key_detection import detect_key
from services.polyphonic.apply_time_signature import apply_time_signature
from services.polyphonic.apply_key_signature import apply_key_to_midi
from services.polyphonic.apply_tempo import apply_tempo
from services.polyphonic.note_duration_normalizer import normalize_note_durations
from services.polyphonic.export_musicxml import midi_to_musicxml
from services.polyphonic.transcribe_audio import transcribe_with_onsets_frames

from services.cross_notation.midi_to_sargam import midi_to_sargam, sargam_string

def run_piano_pipeline(audio_path: str, output_dir: str):
    """
    Complete piano transcription pipeline:
    Audio → Onsets & Frames → MIDI → Quantization → Time/Key → Normalization → MusicXML
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n===== PIANO PIPELINE START =====")

    # --------------------------------------------------
    # STEP 1 — TRANSCRIPTION (Onsets & Frames)
    # --------------------------------------------------
    raw_mid_path = transcribe_with_onsets_frames(audio_path, output_dir)

    # --------------------------------------------------
    # STEP 2 — BEAT TRACKING
    # --------------------------------------------------
    tempo, beat_times = detect_beats(audio_path)

    # --------------------------------------------------
    # STEP 3 — TIME SIGNATURE
    # --------------------------------------------------
    numerator, denominator = detect_time_signature(audio_path, beat_times)

    # --------------------------------------------------
    # STEP 4 — QUANTIZATION
    # --------------------------------------------------
    quant_mid_path = output_dir / "quantized.mid"
    quantize_to_grid(
        str(raw_mid_path),
        beat_times,
        str(quant_mid_path),
        subdivision=4,
        tempo_bpm=tempo,
    )

    # --------------------------------------------------
    # STEP 5 — APPLY TIME SIGNATURE
    # --------------------------------------------------
    ts_mid_path = output_dir / "with_time.mid"
    apply_time_signature(
        str(quant_mid_path),
        numerator,
        denominator,
        str(ts_mid_path),
    )

    # --------------------------------------------------
    # STEP 6 — APPLY TEMPO
    # --------------------------------------------------
    tempo_mid_path = output_dir / "with_tempo.mid"
    apply_tempo(
        str(ts_mid_path),
        tempo,
        str(tempo_mid_path),
    )

    # --------------------------------------------------
    # STEP 7 — KEY DETECTION
    # --------------------------------------------------
    key, mode = detect_key(str(tempo_mid_path))
    key_mid_path = output_dir / "with_key.mid"
    apply_key_to_midi(
        str(tempo_mid_path),
        key,
        mode,
        str(key_mid_path),
    )

    # --------------------------------------------------
    # STEP 8 — NORMALIZE DURATIONS
    # --------------------------------------------------
    norm_mid_path = output_dir / "normalized.mid"

    

    normalize_note_durations(
        str(key_mid_path),
        str(norm_mid_path),
        tempo_bpm=tempo,
    )

    # --------------------------------------------------
    # COPY FINAL MIDI TO OUTPUT DIRECTORY
    # --------------------------------------------------

    final_midi_path = output_dir / "final_piano.mid"
    import shutil
    shutil.copy(norm_mid_path, final_midi_path)

    sargam_notes = midi_to_sargam(str(norm_mid_path), tonic=key, beats_per_measure=numerator)
    sargam_text = sargam_string(sargam_notes, beats_per_measure=numerator, bpm=tempo)

    # --------------------------------------------------
    # STEP 9 — EXPORT MUSICXML
    # --------------------------------------------------
    xml_path = output_dir / "final.musicxml"
    midi_to_musicxml(
        str(norm_mid_path),
        str(xml_path),
        tempo,
    )

    print("===== PIANO PIPELINE COMPLETE =====")
    return {
        "xml": str(xml_path),
        "midi": str(final_midi_path),
        "sargam": sargam_text
    }