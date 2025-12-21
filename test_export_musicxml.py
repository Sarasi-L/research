from backend.services.monophonic.export_musicxml import export_key_aware_notes_to_musicxml

# Example key-aware notes from previous step
key_aware_notes = [
    {"pitch": "B4", "duration_name": "half", "quantized_beats": 1.89},
    {"pitch": "A4", "duration_name": "sixteenth", "quantized_beats": 0.18},
    {"pitch": "G#4", "duration_name": "eighth", "quantized_beats": 0.45},
    {"pitch": "F#4", "duration_name": "eighth", "quantized_beats": 0.55},
    {"pitch": "D#4", "duration_name": "unknown", "quantized_beats": 10.97},
    {"pitch": "E5", "duration_name": "eighth", "quantized_beats": 0.43},
    {"pitch": "F4", "duration_name": "sixteenth", "quantized_beats": 0.16}
]

detected_key = "D# minor"
bpm = 178

export_key_aware_notes_to_musicxml(key_aware_notes, detected_key, bpm, output_file="test_output.musicxml")
