# backend/services/polyphonic/chord_detection.py

import librosa
import numpy as np


CHORD_TEMPLATES = {
    "maj": [0,4,7],
    "min": [0,3,7],
    "dim": [0,3,6],
}


NOTE_NAMES = ['C','C#','D','D#','E','F',
              'F#','G','G#','A','A#','B']


def detect_chords(audio_path, sr=22050):
    y, sr = librosa.load(audio_path, sr=sr)

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    chords = []

    for i in range(chroma.shape[1]):
        frame = chroma[:, i]
        root = np.argmax(frame)

        for chord_type, intervals in CHORD_TEMPLATES.items():
            template = np.zeros(12)
            for interval in intervals:
                template[(root + interval) % 12] = 1

            score = np.dot(frame, template)

            if score > 1.5:
                chord_name = f"{NOTE_NAMES[root]}{chord_type}"
                chords.append(chord_name)
                break

    return chords