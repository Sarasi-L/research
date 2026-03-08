# backend/services/polyphonic/measure_builder.py

from music21 import stream, meter


def build_measures_from_midi(score, numerator=4, denominator=4):

    time_sig = meter.TimeSignature(f"{numerator}/{denominator}")

    structured_score = stream.Score()

    measure_length = time_sig.barDuration.quarterLength

    for part in score.parts:

        new_part = stream.Part()
        new_part.insert(0, time_sig)

        current_measure = stream.Measure(number=1)
        current_length = 0
        measure_number = 1

        for element in part.flat.notesAndRests:

            duration = element.quarterLength

            if current_length + duration > measure_length:

                new_part.append(current_measure)

                measure_number += 1
                current_measure = stream.Measure(number=measure_number)
                current_length = 0

            current_measure.append(element)
            current_length += duration

        if len(current_measure) > 0:
            new_part.append(current_measure)

        structured_score.append(new_part)

    return structured_score