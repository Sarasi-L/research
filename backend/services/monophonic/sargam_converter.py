# backend/services/monophonic/sargam_converter.py

import pretty_midi
from music21 import converter

# ----------------------------------------
# NOTE → Pitch Class
# ----------------------------------------
NOTE_TO_PC = {
    "C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,
    "F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11
}

# ----------------------------------------
# Sargam Mapping
# ----------------------------------------
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

# ----------------------------------------
# STEP 1: XML → MIDI
# ----------------------------------------
def xml_to_midi(xml_path: str, midi_output_path: str):
    score = converter.parse(xml_path)
    score.write("midi", fp=midi_output_path)
    return midi_output_path


# ----------------------------------------
# STEP 2: MIDI → Sargam Notes
# ----------------------------------------
def midi_to_sargam(midi_path: str, tonic: str = "C", beats_per_measure: int = 4):
    midi = pretty_midi.PrettyMIDI(midi_path)

    tonic_clean = tonic.replace(" major", "").replace(" minor", "").strip()
    tonic_pc = NOTE_TO_PC.get(tonic_clean, 0)

    tempo_change_times, tempos = midi.get_tempo_changes()
    bpm = float(tempos[0]) if len(tempos) > 0 else 120.0
    beat_duration = 60.0 / bpm

    notes = []

    for inst in midi.instruments:
        if inst.is_drum:
            continue

        for note in inst.notes:
            pitch_class = note.pitch % 12
            relative_pc = (pitch_class - tonic_pc) % 12
            octave = (note.pitch // 12) - 4

            notes.append({
                "start": float(note.start),
                "end": float(note.end),
                "pitch": note.pitch,
                "sargam": SARGAM_RELATIVE[relative_pc],
                "sargam_short": SARGAM_SHORT[relative_pc],
                "octave": octave,
                "beat": note.start / beat_duration,
                "measure": int(note.start / beat_duration / beats_per_measure),
            })

    notes.sort(key=lambda x: x["start"])
    return notes, bpm


# ----------------------------------------
# STEP 3: FORMAT SARGAM STRING
# ----------------------------------------
def sargam_string(notes: list, beats_per_measure=4, bpm=120.0):
    if not notes:
        return ""

    beat_duration = 60.0 / bpm
    measure_duration = beat_duration * beats_per_measure

    result = []
    current_measure = -1
    measure_count = 0

    for n in notes:
        measure = int(n["start"] / measure_duration)

        if measure != current_measure:
            if current_measure >= 0:
                result.append("|")
                measure_count += 1
                if measure_count % 4 == 0:
                    result.append("\n")
            current_measure = measure

        syllable = n["sargam_short"]

        octave = n.get("octave", 0)
        if octave > 0:
            syllable += "'" * octave
        elif octave < 0:
            syllable += "," * abs(octave)

        result.append(syllable)

    if result and result[-1] not in ["|", "\n"]:
        result.append("|")

    # formatting
    output = ""
    for token in result:
        if token in ("|", "\n"):
            output += " " + token + " "
        else:
            output += token + " "

    return output.strip()


# ----------------------------------------
# MAIN PIPELINE
# ----------------------------------------
def convert_xml_to_sargam(xml_path: str, key="C", beats_per_measure=4):
    """
    FULL MONOPHONIC SARGAM PIPELINE
    XML → MIDI → Sargam
    """

    midi_path = xml_path.replace(".musicxml", ".mid")

    # Step 1
    xml_to_midi(xml_path, midi_path)

    # Step 2
    notes, bpm = midi_to_sargam(
        midi_path,
        tonic=key,
        beats_per_measure=beats_per_measure
    )

    # Step 3
    sargam_text = sargam_string(notes, beats_per_measure, bpm)

    return {
        "notes": notes,
        "bpm": bpm,
        "sargam_text": sargam_text
    }