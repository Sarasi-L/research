# convert_gt_xml.py

from music21 import converter

score = converter.parse("valipoly/MIDI-Unprocessed_01_R1_2011_MID--AUDIO_R1-D1_02_Track02_wav.mid")

score.write("musicxml", "groundtruth.musicxml")

print("Ground truth XML created")