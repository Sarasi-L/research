from music21 import converter
score = converter.parse("flute_keyboard_guitar_sequential.musicxml")
score.show("text")
