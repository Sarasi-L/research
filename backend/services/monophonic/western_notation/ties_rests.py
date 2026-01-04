# backend/services/monophonic/western_notation/ties_rests.py

def apply_ties_and_rests(measures, beats_per_measure):
    """Apply ties if notes exceed measure, insert rests if needed"""
    new_measures = []
    for m in measures:
        current_sum = sum(n["quantized_beats"] for n in m)
        if current_sum < beats_per_measure:
            # Add rest dynamically
            m.append({"pitch": 0, "quantized_beats": beats_per_measure - current_sum, "note_name": "Rest"})
        # Handle ties
        for n in m:
            if n["quantized_beats"] > beats_per_measure:
                n["tie"] = "start"  # dynamically
        new_measures.append(m)
    return new_measures
