from backend.services.monophonic.western_notation.measure_grouping import group_notes_into_measures

# Test notes with quantized beats
test_notes = [{"quantized_beats": 1} for _ in range(10)]
measures = group_notes_into_measures(test_notes, beats_per_measure=4)

for i, m in enumerate(measures):
    total_beats = sum(n['quantized_beats'] for n in m)
    print(f"Measure {i+1}: {len(m)} notes, total beats = {total_beats}")
# ✅ Check that no measure exceeds 4 beats
