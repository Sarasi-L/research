#backend/services/polyphonic/staff_splitter.py

from music21 import stream, clef


def split_grand_staff(score):
    """
    Split notes into treble and bass staff by pitch.
    """

    treble = stream.Part()
    bass = stream.Part()

    treble.insert(0, clef.TrebleClef())
    bass.insert(0, clef.BassClef())

    for n in score.flat.notes:
        if n.pitch.midi >= 60:
            treble.append(n)
        else:
            bass.append(n)

    new_score = stream.Score()
    new_score.append(treble)
    new_score.append(bass)

    return new_score