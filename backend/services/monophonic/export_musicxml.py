from music21 import stream, note, meter, key, tempo

def export_key_aware_notes_to_musicxml(notes, detected_key, bpm=120, output_file="output.musicxml"):
    """
    Convert key-aware notes into MusicXML using music21
    """
    s = stream.Score()
    p = stream.Part()
    
    # Set tempo
    mm = tempo.MetronomeMark(number=bpm)
    p.append(mm)
    
    # Split key into tonic and mode
    tonic, mode = detected_key.split()  # e.g., "D#" "minor"
    key_sig = key.Key(tonic, mode=mode)
    p.append(key_sig)

    # Default 4/4 time signature
    ts = meter.TimeSignature('4/4')
    p.append(ts)

    for n in notes:
        pitch_name = n['pitch']  # e.g., "C4"
        dur = n['quantized_beats']

        if n['duration_name'] == "unknown" or dur is None:
            dur = 1.0  # default to quarter note

        m21_note = note.Note(pitch_name)
        m21_note.quarterLength = dur
        p.append(m21_note)

    s.append(p)
    s.write('musicxml', fp=output_file)
    print(f"MusicXML exported to {output_file}")
