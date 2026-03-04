import librosa
import numpy as np
from music21 import converter, note, chord


# ------------------------------------------------
# 1. Extract MIDI Pitch Sequence (Robust Version)
# ------------------------------------------------
def extract_midi_pitch_sequence(midi_path):

    try:
        score = converter.parse(midi_path)
    except Exception as e:
        print(f"❌ Error loading MIDI: {e}")
        return np.array([])

    pitch_seq = []

    for element in score.recurse().notesAndRests:

        # Single note
        if isinstance(element, note.Note):
            pitch_seq.append(element.pitch.midi)

        # Chord (including PercussionChord)
        elif isinstance(element, chord.Chord):
            for p in element.pitches:
                pitch_seq.append(p.midi)

        # Ignore rests automatically

    return np.array(pitch_seq)


# ------------------------------------------------
# 2. Extract Audio Pitch Sequence
# ------------------------------------------------
def extract_audio_pitch_sequence(audio_path):

    try:
        y, sr = librosa.load(audio_path)
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return np.array([])

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    pitch_seq = []

    for t in range(pitches.shape[1]):

        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]

        if pitch > 0:
            midi_pitch = librosa.hz_to_midi(pitch)
            pitch_seq.append(midi_pitch)

    return np.array(pitch_seq)


# ------------------------------------------------
# 3. Compare Audio vs MIDI Pitch Sequences
# ------------------------------------------------
def compare_audio_midi(audio_path, midi_path):

    print("\n[VALIDATION] ===== Audio vs MIDI Comparison =====")

    midi_seq = extract_midi_pitch_sequence(midi_path)
    audio_seq = extract_audio_pitch_sequence(audio_path)

    if len(midi_seq) == 0:
        print("❌ No MIDI pitches extracted.")
        return None

    if len(audio_seq) == 0:
        print("❌ No audio pitches extracted.")
        return None

    # Match lengths safely
    min_len = min(len(midi_seq), len(audio_seq))

    midi_seq = midi_seq[:min_len]
    audio_seq = audio_seq[:min_len]

    # Avoid NaN correlation
    if np.std(midi_seq) == 0 or np.std(audio_seq) == 0:
        print("⚠️ Cannot compute correlation (constant sequence).")
        return None

    correlation = np.corrcoef(midi_seq, audio_seq)[0, 1]

    print(f"Total Compared Frames: {min_len}")
    print(f"Pitch Correlation: {correlation:.3f}")

    return correlation


# ------------------------------------------------
# 4. Run Directly (Testing)
# ------------------------------------------------
if __name__ == "__main__":

    audio_file = "backend/audio_output/generated_audio.wav"
    midi_file = "backend/midi_output/full_song_key_ts.mid"

    compare_audio_midi(audio_file, midi_file)