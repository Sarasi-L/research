from backend.services.monophonic.western_notation.ties_rests import fill_measure_with_rests, split_note_for_bar

# Test filling rests
measure = [{"note_name": "C4", "quantized_beats": 3}]
measure_filled = fill_measure_with_rests(measure)
print("Measure after filling rests:", measure_filled)
# ✅ Should include 1 beat rest

# Test splitting notes across bars
note_to_split = {"note_name": "G4", "quantized_beats": 5}
split_notes = split_note_for_bar(note_to_split, remaining_beats=4)
print("Split Notes:", split_notes)
# ✅ First note 4 beats tie start, second note 1 beat tie stop
