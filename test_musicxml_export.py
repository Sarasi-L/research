from backend.services.monophonic.western_notation.musicxml_export import export_musicxml

# Sample measures
test_measures = [
    [{"note_name": "C4", "quantized_beats": 2}, {"note_name": "D4", "quantized_beats": 2}],
    [{"note_name": "E4", "quantized_beats": 4}]
]

export_musicxml(test_measures, bpm=120, time_signature="4/4", filename="test_output.musicxml")
print("Check 'test_output.musicxml' in MuseScore or music21.show()")
