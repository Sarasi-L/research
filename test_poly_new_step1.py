# test_poly_new_full_pipeline.py

from pathlib import Path

from backend.services.polyphonic.separate_demucs import separate_polyphonic
from backend.services.polyphonic.transcribe_basic_pitch import transcribe_stem
from backend.services.polyphonic.transcribe_drums import transcribe_drums
from backend.services.polyphonic.beat_tracking import detect_beats
from backend.services.polyphonic.quantize_midi import quantize_midi
from backend.services.polyphonic.merge_midi import merge_midi_tracks

from backend.services.polyphonic.key_detection import detect_key
from backend.services.polyphonic.apply_key_signature import apply_key_to_midi

from backend.services.polyphonic.time_signature import detect_time_signature
from backend.services.polyphonic.apply_time_signature import apply_time_signature

from backend.services.polyphonic.export_musicxml import midi_to_musicxml


INPUT_AUDIO = "mix3poly.mp3"
OUTPUT_DIR = Path("backend/midi_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_MIDI_DIR = "backend/midi_raw"
QUANT_MIDI_DIR = "backend/midi_quantized"

Path(RAW_MIDI_DIR).mkdir(parents=True, exist_ok=True)
Path(QUANT_MIDI_DIR).mkdir(parents=True, exist_ok=True)

print("\n===== STEP 1: Demucs Separation =====")
stems = separate_polyphonic(INPUT_AUDIO, "backend/stems")

print("\n===== STEP 2: Transcription =====")
raw_midis = {}

for stem_name, stem_path in stems.items():
    if stem_name == "drums":
        midi_path = transcribe_drums(stem_path, RAW_MIDI_DIR)
    else:
        midi_path = transcribe_stem(stem_path, RAW_MIDI_DIR)

    raw_midis[stem_name] = midi_path

print("\n===== STEP 3: Beat Tracking =====")
tempo, beat_times = detect_beats(INPUT_AUDIO)

print("\n===== STEP 4: Quantizing =====")
quantized_midis = {}

for name, midi_path in raw_midis.items():
    quant_path = f"{QUANT_MIDI_DIR}/{name}_quant.mid"
    q_midi = quantize_midi(midi_path, beat_times, quant_path)
    quantized_midis[name] = q_midi

print("\n===== STEP 5: Merging Quantized Tracks =====")
merged_midi_path = merge_midi_tracks(
    quantized_midis, OUTPUT_DIR / "full_song_quant.mid"
)

print("\n===== STEP 6: Key Detection =====")
key, mode = detect_key(merged_midi_path)

key_midi_path = OUTPUT_DIR / "full_song_key.mid"
apply_key_to_midi(merged_midi_path, key, mode, key_midi_path)

print("\n===== STEP 7: Time Signature Detection =====")
num, den = detect_time_signature(INPUT_AUDIO, beat_times)

ts_midi_path = OUTPUT_DIR / "full_song_key_ts.mid"
apply_time_signature(str(key_midi_path), num, den, ts_midi_path)

print("\n===== STEP 8: Export to MusicXML =====")
xml_path = OUTPUT_DIR / "full_song.xml"
midi_to_musicxml(str(ts_midi_path), str(xml_path))

print("\n🎉 PIPELINE COMPLETE — MIDI + MUSICXML READY\n")