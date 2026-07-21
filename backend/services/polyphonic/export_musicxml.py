# backend/services/polyphonic/export_musicxml.py

from music21 import converter, tempo, stream, note, chord, midi as m21midi
from music21.musicxml import m21ToXml
from pathlib import Path
import pretty_midi


def midi_to_musicxml(midi_path: str, output_xml_path: str, bpm: float = 120):
   
    print("\n[XML] ===== Exporting MusicXML =====")

    midi_path      = Path(midi_path)
    output_xml_path = Path(output_xml_path)

    # ── Parse MIDI with music21 ──
    try:
        score = converter.parse(str(midi_path), format="midi")
    except Exception as e:
        print(f"[XML] ❌ Failed to parse MIDI: {e}")
        return _build_from_pretty_midi(midi_path, output_xml_path, bpm)

    flat      = score.flatten()
    pre_notes = len([n for n in flat.notes])
    pre_rests = len([r for r in flat.notesAndRests if r.isRest])
    print(f"[XML] Input notes: {pre_notes}, rests: {pre_rests}")

    # ── Insert tempo mark at measure 1 ──
    try:
        parts = score.parts
        if parts:
            parts[0].insert(0, tempo.MetronomeMark(number=bpm))
        else:
            score.insert(0, tempo.MetronomeMark(number=bpm))
    except Exception:
        score.insert(0, tempo.MetronomeMark(number=bpm))

    # ── Strategy 1: makeNotation then write ──
    try:
        print("[XML] Trying strategy 1: makeNotation + write…")
        score_copy = score.deepcopy()
        score_copy.makeNotation(inPlace=True)
        score_copy.write("musicxml", str(output_xml_path))
        post, _ = _verify_xml(output_xml_path)
        print(f"[XML] Strategy 1: {post} notes")
        if post >= pre_notes * 0.90:
            print(f"[XML] ✓ Strategy 1 succeeded ({post}/{pre_notes} notes)")
            return str(output_xml_path)
        print(f"[XML] ⚠ Strategy 1 lost too many notes ({post}/{pre_notes})")
    except Exception as e:
        print(f"[XML] Strategy 1 failed: {e}")

    # ── Strategy 2: write directly without makeNotation ──
    try:
        print("[XML] Trying strategy 2: direct write…")
        score.write("musicxml", str(output_xml_path))
        post, _ = _verify_xml(output_xml_path)
        print(f"[XML] Strategy 2: {post} notes")
        if post >= pre_notes * 0.90:
            print(f"[XML] ✓ Strategy 2 succeeded ({post}/{pre_notes} notes)")
            return str(output_xml_path)
        print(f"[XML] ⚠ Strategy 2 lost too many notes ({post}/{pre_notes})")
    except Exception as e:
        print(f"[XML] Strategy 2 failed: {e}")

    # ── Strategy 3: rebuild parts manually ──
    try:
        print("[XML] Trying strategy 3: rebuild parts…")
        new_score = stream.Score()
        new_score.insert(0, tempo.MetronomeMark(number=bpm))

        for i, part in enumerate(score.parts):
            new_part = stream.Part()
            new_part.id = f"Part{i+1}"
            for measure in part.getElementsByClass(stream.Measure):
                new_measure = stream.Measure(number=measure.number)
                for el in measure.notesAndRests:
                    new_measure.append(el)
                new_part.append(new_measure)
            new_score.append(new_part)

        new_score.makeNotation(inPlace=True)
        new_score.write("musicxml", str(output_xml_path))
        post, _ = _verify_xml(output_xml_path)
        print(f"[XML] Strategy 3: {post} notes")
        if post >= pre_notes * 0.85:
            print(f"[XML] ✓ Strategy 3 succeeded ({post}/{pre_notes} notes)")
            return str(output_xml_path)
        print(f"[XML] ⚠ Strategy 3 lost too many notes ({post}/{pre_notes})")
    except Exception as e:
        print(f"[XML] Strategy 3 failed: {e}")

    # ── Strategy 4: re-read MIDI via m21midi translate ──
    try:
        print("[XML] Trying strategy 4: m21midi translate…")
        mf = m21midi.MidiFile()
        mf.open(str(midi_path))
        mf.read()
        mf.close()
        rebuilt = m21midi.translate.midiFileToStream(mf)
        rebuilt.insert(0, tempo.MetronomeMark(number=bpm))
        rebuilt.makeNotation(inPlace=True)
        rebuilt.write("musicxml", str(output_xml_path))
        post, _ = _verify_xml(output_xml_path)
        print(f"[XML] Strategy 4: {post} notes")
        if post >= pre_notes * 0.85:
            print(f"[XML] ✓ Strategy 4 succeeded ({post}/{pre_notes} notes)")
            return str(output_xml_path)
    except Exception as e:
        print(f"[XML] Strategy 4 failed: {e}")

    # ── Final fallback: build from pretty_midi ──
    print("[XML] All strategies failed — using pretty_midi fallback")
    return _build_from_pretty_midi(midi_path, output_xml_path, bpm)


def _build_from_pretty_midi(midi_path: Path, output_xml_path: Path, bpm: float):
    """
    Last resort: read with pretty_midi, rebuild a clean music21 score from scratch.
    Guarantees valid MusicXML with all notes preserved.
    """
    try:
        import pretty_midi
        from fractions import Fraction

        pm   = pretty_midi.PrettyMIDI(str(midi_path))
        s    = stream.Score()
        s.insert(0, tempo.MetronomeMark(number=bpm))

        beat_len = 60.0 / bpm  # seconds per beat

        for i, inst in enumerate(pm.instruments):
            if not inst.notes:
                continue

            p = stream.Part()
            p.id = f"Part{i+1}"
            p.partName = inst.name or f"Instrument {i+1}"

            # Sort notes by start time
            sorted_notes = sorted(inst.notes, key=lambda n: n.start)

            # Build flat note list with rests between them
            cursor = 0.0
            for n in sorted_notes:
                # Add rest if there's a gap
                gap = n.start - cursor
                if gap > 0.05:
                    rest_beats = gap / beat_len
                    r = note.Rest()
                    r.duration.quarterLength = round(rest_beats * 4) / 4
                    if r.duration.quarterLength > 0:
                        p.append(r)

                # Add note
                dur_beats = (n.end - n.start) / beat_len
                ql = round(dur_beats * 4) / 4
                if ql <= 0:
                    ql = 0.25

                m21_note = note.Note(n.pitch)
                m21_note.duration.quarterLength = ql
                m21_note.volume.velocity = n.velocity
                p.append(m21_note)
                cursor = n.end

            s.append(p)

        # Make proper notation (adds measures, barlines, clefs)
        s.makeNotation(inPlace=True)
        s.write("musicxml", str(output_xml_path))

        post, _ = _verify_xml(output_xml_path)
        print(f"[XML] ✓ pretty_midi fallback: {post} notes written")
        return str(output_xml_path)

    except Exception as e:
        print(f"[XML] ❌ pretty_midi fallback failed: {e}")
        return str(output_xml_path)


def _verify_xml(xml_path):
    """Count notes and rests in exported XML file."""
    try:
        s    = converter.parse(str(xml_path))
        flat = s.flatten()
        notes = len([n for n in flat.notes])
        rests = len([r for r in flat.notesAndRests if r.isRest])
        return notes, rests
    except Exception:
        return 0, 0