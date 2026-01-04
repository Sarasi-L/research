# backend/services/monophonic/western_notation/measure_grouping.py

def group_notes_into_measures(notes, beats_per_measure):
    """
    Group quantized notes into measures based on beats per measure.

    Uses a small epsilon to avoid floating-point overflow issues
    that cause phantom rests or premature measure breaks.
    """

    measures = []
    current_measure = []
    current_sum = 0.0

    EPS = 1e-3  # floating-point tolerance

    for n in notes:
        dur = float(n.get("quantized_beats", 0.0))

        # Check if note fits in current measure (with tolerance)
        if current_sum + dur <= beats_per_measure + EPS:
            current_measure.append(n)
            current_sum += dur
        else:
            # Close current measure
            measures.append(current_measure)

            # Start new measure
            current_measure = [n]
            current_sum = dur

    # Append last measure
    if current_measure:
        measures.append(current_measure)

    return measures
