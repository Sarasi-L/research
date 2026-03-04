# backend/services/polyphonic/export_musicxml.py

from music21 import converter
from pathlib import Path

def midi_to_musicxml(midi_path: str, output_xml_path: str):
    """
    Convert MIDI to MusicXML using music21.
    """

    print("\n[XML] ===== Exporting MusicXML =====")

    midi_path = Path(midi_path)
    output_xml_path = Path(output_xml_path)

    # 🔧 IMPORTANT FIX: explicitly tell music21 it's MIDI
    score = converter.parse(str(midi_path), format='midi')

    score.write("musicxml", str(output_xml_path))

    print(f"[XML] ✓ MusicXML exported to: {output_xml_path}")

    return str(output_xml_path)