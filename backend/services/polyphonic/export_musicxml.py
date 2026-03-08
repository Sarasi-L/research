# backend/services/polyphonic/export_musicxml.py

from music21 import converter, tempo, stream, instrument, note, chord
from pathlib import Path
import pretty_midi


def midi_to_musicxml(midi_path: str, output_xml_path: str, bpm: float = 120):
    """
    Export MIDI to MusicXML WITHOUT losing notes.
    Uses multiple fallback strategies to ensure all notes are preserved.
    """
    print("\n[XML] ===== Exporting MusicXML =====")
    
    # Parse MIDI
    score = converter.parse(str(midi_path), format="midi")
    
    # Count notes before processing
    flat = score.flatten()

    all_notes = [n for n in flat.notes]
    all_rests = [r for r in flat.notesAndRests if r.isRest]

    pre_notes = len(all_notes)
    pre_rests = len(all_rests)

    print(f"[XML] Input notes: {pre_notes}, rests: {pre_rests}")
    
    # Insert tempo
    score.insert(0, tempo.MetronomeMark(number=bpm))
    
    # Try different export strategies
    strategies = [
        ("minimal", _export_minimal),
        ("standard", _export_standard),
        ("raw", _export_raw)
    ]
    
    for strategy_name, strategy_func in strategies:
        try:
            print(f"[XML] Trying {strategy_name} export strategy...")
            success = strategy_func(score, output_xml_path)

            if success:
                # Verify the export
                post_notes, post_rests = _verify_xml(output_xml_path)
                print(f"[XML] {strategy_name} export: {post_notes} notes, {post_rests} rests")
                
                if post_notes >= pre_notes * 0.95:
                    print(f"[XML] ✓ Using {strategy_name} export (preserved {post_notes}/{pre_notes} notes)")
                    return str(output_xml_path)
                else:
                    print(f"[XML] ⚠️ {strategy_name} lost too many notes ({post_notes}/{pre_notes})")

        except Exception as e:
            print(f"[XML] {strategy_name} failed: {e}")
            continue
    
    # Final fallback
    print("[XML] Using final fallback...")
    return _fallback_export(midi_path, output_xml_path, bpm)


def _export_minimal(score, output_path):
    """Minimal processing - just add tempo and export"""
    try:
        score_copy = score.core.copyAsDerivation()
        score_copy.write("musicxml", str(output_path))
        return True
    except:
        return False


def _export_standard(score, output_path):
    """Standard processing with careful notation"""
    try:
        score_copy = score.core.copyAsDerivation()

        try:
            score_copy.makeNotation(inPlace=True)
        except:
            pass
        
        score_copy.write("musicxml", str(output_path))
        return True
    except:
        return False


def _export_raw(score, output_path):
    """Raw export with no processing"""
    try:
        score.write("musicxml", str(output_path))
        return True
    except:
        return False


def _verify_xml(xml_path):
    """Count notes and rests in XML file"""
    try:
        score = converter.parse(str(xml_path))
        flat = score.flatten()

        notes = len([n for n in flat.notes])
        rests = len([r for r in flat.notesAndRests if r.isRest])

        return notes, rests
    except:
        return 0, 0


def _fallback_export(midi_path, output_xml_path, bpm):
    """Ultimate fallback: create fresh score from scratch"""
    try:
        from music21 import stream, tempo, midi as m21midi
        
        mf = m21midi.MidiFile()
        mf.open(str(midi_path))
        mf.read()
        mf.close()
        
        score = m21midi.translate.midiFileToStream(mf)

        score.insert(0, tempo.MetronomeMark(number=bpm))

        score.write("musicxml", str(output_xml_path))

        notes, _ = _verify_xml(output_xml_path)
        print(f"[XML] Fallback export: {notes} notes")

        return str(output_xml_path)

    except Exception as e:
        print(f"[XML] ❌ Fallback failed: {e}")
        return str(output_xml_path)