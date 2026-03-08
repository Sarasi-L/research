# generate_gt_xml_all.py
# Convert all MAESTRO ground-truth MIDI files used in testing to MusicXML

from pathlib import Path
from music21 import converter
import os


# ================================
# PATHS (match your project)
# ================================

PROJECT_ROOT = Path(__file__).resolve().parent

MAESTRO_MIDI_DIR = PROJECT_ROOT / "maestro"
EVAL_OUTPUT_DIR = PROJECT_ROOT / "eval_outputs"
GT_XML_DIR = PROJECT_ROOT / "groundtruth_xml"


# create output folder
GT_XML_DIR.mkdir(exist_ok=True)


# ================================
# Find tested songs
# ================================

print("\nScanning evaluation outputs...")

tested_songs = []

for folder in EVAL_OUTPUT_DIR.iterdir():

    if folder.is_dir():
        song_name = folder.name

        midi_path = MAESTRO_MIDI_DIR / f"{song_name}.mid"

        if midi_path.exists():
            tested_songs.append((song_name, midi_path))


print(f"Found {len(tested_songs)} tested songs.\n")


# ================================
# Convert MIDI → XML
# ================================

for i, (song_name, midi_path) in enumerate(tested_songs, start=1):

    print(f"[{i}/{len(tested_songs)}] {song_name}")

    xml_out = GT_XML_DIR / f"{song_name}.musicxml"

    try:
        score = converter.parse(str(midi_path))

        score.write("musicxml", str(xml_out))

        print(f"  ✓ XML created → {xml_out}")

    except Exception as e:

        print(f"  ❌ Failed: {e}")


print("\nAll ground-truth XML files generated.")