# backend/services/monophonic/western_notation/musicxml_export.py

from music21 import stream, note, meter, key, tempo, tie

# MusicXML-safe durations
ALLOWED_DURATIONS = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.25]

def sanitize_duration(d):
    """Force duration to nearest MusicXML-safe value"""
    return min(ALLOWED_DURATIONS, key=lambda x: abs(x - d))


def generate_musicxml(
    western_measures,
    tempo_bpm,
    key_name,
    beats_per_measure,
    output_file
):
    """
    Generate MusicXML from Western notation measures
    """

    # --------------------
    # Score & Part
    # --------------------
    score = stream.Score()
    part = stream.Part()

    # --------------------
    # Tempo
    # --------------------
    try:
        part.append(tempo.MetronomeMark(number=float(tempo_bpm)))
    except Exception:
        part.append(tempo.MetronomeMark(number=120))

    # --------------------
    # Key Signature
    # --------------------
    try:
        parts = key_name.split()
        if len(parts) == 2:
            k = key.Key(parts[0], parts[1])
        else:
            k = key.Key(key_name)
        part.append(k)
    except Exception:
        part.append(key.Key("C"))

    # --------------------
    # Time Signature
    # --------------------
    try:
        ts = meter.TimeSignature(f"{beats_per_measure}/4")
    except Exception:
        ts = meter.TimeSignature("4/4")
    part.append(ts)

    # --------------------
    # Measures
    # --------------------
    for measure_notes in western_measures:
        m = stream.Measure()
        current_beats = 0.0

        for n in measure_notes:
            raw_duration = float(n.get("quantized_beats", 1.0))
            duration = sanitize_duration(raw_duration)

            # Prevent overflow
            if current_beats + duration > beats_per_measure:
                duration = sanitize_duration(
                    beats_per_measure - current_beats
                )

            current_beats += duration

            note_name = n.get("note_name")

            # -------- REST --------
            if note_name in {None, "", "R", "REST", "SILENCE"}:
                m.append(note.Rest(quarterLength=duration))
                continue

            # -------- NOTE --------
            try:
                nn = str(note_name).strip()
                n_obj = note.Note(nn)
                n_obj.quarterLength = duration

                if n.get("tie") == "start":
                    n_obj.tie = tie.Tie("start")
                elif n.get("tie") == "stop":
                    n_obj.tie = tie.Tie("stop")

                m.append(n_obj)

            except Exception:
                # Invalid pitch → rest
                m.append(note.Rest(quarterLength=duration))

        part.append(m)

    # --------------------
    # Write MusicXML
    # --------------------
    score.append(part)
    score.write("musicxml", fp=output_file)

    return output_file
