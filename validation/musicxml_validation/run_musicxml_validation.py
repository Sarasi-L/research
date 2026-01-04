import music21

score = music21.converter.parse("mono6o.musicxml")
score.show('text')
