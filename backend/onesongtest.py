# backend/test_single_mp3_to_xml.py
# Convert one piano MP3 to MusicXML using your pipeline

from pathlib import Path
import shutil
import numpy as np
import pretty_midi

from services.polyphonic.multipitch_detection import detect_multipitch
from services.polyphonic.quantize_midi import quantize_to_grid
from services.polyphonic.beat_tracking import detect_beats
from services.polyphonic.time_signature import detect_time_signature
from services.polyphonic.key_detection import detect_key
from services.polyphonic.apply_time_signature import apply_time_signature
from services.polyphonic.apply_key_signature import apply_key_to_midi
from services.polyphonic.apply_tempo import apply_tempo
from services.polyphonic.note_duration_normalizer import normalize_note_durations
from services.polyphonic.export_musicxml import midi_to_musicxml


# =====================================================
# CONFIG
# =====================================================

AUDIO_FILE = "national-anthem.mp3"   # your piano MP3
OUTPUT_DIR = Path("xml_output")


# =====================================================
# STEP 1 — TRANSCRIBE AUDIO → MIDI
# =====================================================

def transcribe(audio_path, output_dir):

    print("\n[1] Multi-pitch transcription")

    notes = detect_multipitch(audio_path, post_process=True)

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    for n in notes:

        velocity = int(np.clip(n["velocity"] * 127, 30, 110))

        note = pretty_midi.Note(
            velocity=velocity,
            pitch=n["pitch"],
            start=n["onset"],
            end=n["offset"]
        )

        instrument.notes.append(note)

    midi.instruments.append(instrument)

    raw_mid = output_dir / "raw.mid"
    midi.write(str(raw_mid))

    print(f"Notes detected: {len(notes)}")

    return raw_mid


# =====================================================
# MAIN PIPELINE
# =====================================================

def run_pipeline():

    audio_path = AUDIO_FILE

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True)

    print("\n========== PIANO TRANSCRIPTION ==========")

    # STEP 1
    raw_mid = transcribe(audio_path, OUTPUT_DIR)

    # STEP 2 Beat tracking
    print("\n[2] Beat tracking")

    tempo, beat_times = detect_beats(audio_path)

    print("Tempo:", tempo)

    # STEP 3 Time signature
    print("\n[3] Time signature")

    numerator, denominator = detect_time_signature(audio_path, beat_times)

    print(f"Time signature: {numerator}/{denominator}")

    # STEP 4 Quantize
    print("\n[4] Quantization")

    quantized_mid = OUTPUT_DIR / "quantized.mid"

    quantize_to_grid(
        str(raw_mid),
        beat_times,
        str(quantized_mid),
        subdivision=4,
        tempo_bpm=tempo
    )

    # STEP 5 Apply time signature
    ts_mid = OUTPUT_DIR / "time.mid"

    apply_time_signature(
        str(quantized_mid),
        numerator,
        denominator,
        str(ts_mid)
    )

    # STEP 6 Apply tempo
    tempo_mid = OUTPUT_DIR / "tempo.mid"

    apply_tempo(str(ts_mid), tempo, str(tempo_mid))

    # STEP 7 Key detection
    print("\n[5] Key detection")

    key, mode = detect_key(str(tempo_mid))

    print("Key:", key, mode)

    key_mid = OUTPUT_DIR / "key.mid"

    apply_key_to_midi(
        str(tempo_mid),
        key,
        mode,
        str(key_mid)
    )

    # STEP 8 Normalize durations
    print("\n[6] Duration normalization")

    normalized_mid = OUTPUT_DIR / "final.mid"

    normalize_note_durations(
        str(key_mid),
        str(normalized_mid),
        tempo_bpm=tempo
    )

    # STEP 9 Export XML
    print("\n[7] Export MusicXML")

    xml_file = OUTPUT_DIR / "piano_score.musicxml"

    midi_to_musicxml(
        str(normalized_mid),
        str(xml_file),
        tempo
    )

    print("\n✅ DONE")
    print("MusicXML file:", xml_file)


# =====================================================

if __name__ == "__main__":
    run_pipeline()