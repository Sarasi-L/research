import pretty_midi

NOTE_TO_PC = {
    "C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,
    "F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11
}

SARGAM_RELATIVE = {
    0:  "Sa",
    1:  "komal Re",
    2:  "Re",
    3:  "komal Ga",
    4:  "Ga",
    5:  "Ma",
    6:  "Tivra Ma",
    7:  "Pa",
    8:  "komal Dha",
    9:  "Dha",
    10: "komal Ni",
    11: "Ni"
}

# Short display versions for the UI colored syllables
SARGAM_SHORT = {
    0:  "Sa",
    1:  "Re♭",
    2:  "Re",
    3:  "Ga♭",
    4:  "Ga",
    5:  "Ma",
    6:  "Ma♯",
    7:  "Pa",
    8:  "Dha♭",
    9:  "Dha",
    10: "Ni♭",
    11: "Ni"
}


def midi_to_sargam(midi_path: str, tonic: str = "C", beats_per_measure: int = 4):
    """
    Convert MIDI to Sargam notes with timing and measure information.
    Returns list of note dicts with start, end, sargam, beat position.
    """
    try:
        midi = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        print(f"[SARGAM] Failed to load MIDI: {e}")
        return []

    # Normalize tonic — handle enharmonics and sharps like "G#"
    tonic_clean = tonic.replace(" major", "").replace(" minor", "").strip()
    tonic_pc = NOTE_TO_PC.get(tonic_clean, 0)

    # Get tempo for beat calculation
    tempo_change_times, tempos = midi.get_tempo_changes()
    bpm = float(tempos[0]) if len(tempos) > 0 else 120.0
    beat_duration = 60.0 / bpm  # seconds per beat

    notes = []
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for note in inst.notes:
            pitch_class = note.pitch % 12
            relative_pc = (pitch_class - tonic_pc) % 12
            octave = (note.pitch // 12) - 4  # relative to middle octave

            notes.append({
                "start":      float(note.start),
                "end":        float(note.end),
                "pitch":      note.pitch,
                "sargam":     SARGAM_RELATIVE[relative_pc],
                "sargam_short": SARGAM_SHORT[relative_pc],
                "octave":     octave,
                "beat":       note.start / beat_duration,
                "measure":    int(note.start / beat_duration / beats_per_measure),
                "pc":         relative_pc,
            })

    notes.sort(key=lambda x: x["start"])
    return notes


def sargam_string(notes: list, beats_per_measure: int = 4, bpm: float = 120.0) -> str:
    """
    Build a formatted Sargam string with:
    - Measure bar markers  |
    - Newlines every 4 measures
    - Octave markers: ' for upper, , for lower
    """
    if not notes:
        return ""

    beat_duration = 60.0 / bpm
    measure_duration = beat_duration * beats_per_measure

    result = []
    current_measure = -1
    measure_count = 0

    for n in notes:
        if not n.get("sargam_short"):
            continue

        measure = int(n["start"] / measure_duration) if measure_duration > 0 else 0

        # Add bar marker when measure changes
        if measure != current_measure:
            if current_measure >= 0:
                result.append("|")
                measure_count += 1
                # New line every 4 measures for readability
                if measure_count % 4 == 0:
                    result.append("\n")
            current_measure = measure

        # Build syllable with octave marker
        syllable = n["sargam_short"]
        octave = n.get("octave", 0)
        if octave > 0:
            syllable += "'" * octave       # upper octave dots
        elif octave < 0:
            syllable += "," * abs(octave)  # lower octave commas

        result.append(syllable)

    # Close final measure
    if result and result[-1] != "|" and result[-1] != "\n":
        result.append("|")

    # Join — bars get no space around them, notes get spaces
    output = ""
    for i, token in enumerate(result):
        if token in ("|", "\n"):
            output += " " + token + " "
        else:
            output += token + " "

    return output.strip()