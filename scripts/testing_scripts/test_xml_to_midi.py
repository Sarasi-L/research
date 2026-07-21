from music21 import converter
score = converter.parse('test_output.musicxml')
score.show('midi')
