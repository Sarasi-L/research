import music21

def validate_musicxml(path):
    checks = []

    # 1. Can it be parsed?
    try:
        score = music21.converter.parse(path)
        checks.append(True)
    except Exception as e:
        print("Parse failed:", e)
        return 0.0

    # 2. Time signature exists
    time_sigs = score.recurse().getElementsByClass('TimeSignature')
    checks.append(len(time_sigs) > 0)

    # 3. Measure duration validity
    try:
        part = score.parts[0]
        for m in part.getElementsByClass('Measure'):
            dur = sum(n.quarterLength for n in m.notesAndRests)
            checks.append(abs(dur - m.barDuration.quarterLength) < 0.01)
    except:
        checks.append(False)

    # 4. No overlapping notes
    try:
        offsets = []
        for n in part.notes:
            offsets.append((n.offset, n.offset + n.quarterLength))
        checks.append(len(offsets) == len(set(offsets)))
    except:
        checks.append(False)

    return sum(checks) / len(checks)


if __name__ == "__main__":
    musicxml_path = "mono6o.musicxml"
    score = validate_musicxml(musicxml_path)
    print("MusicXML Validity Score:", round(score, 3))
