# test_validate_notes.py

from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.validation.validate_notes import validate_note_segmentation

if __name__ == "__main__":
    audio_file = "mix7.mp3"
    y, sr = preprocess_audio(audio_file, instrument="flute")  # get waveform

    metrics = validate_note_segmentation(y, sr)

    print("\n[RESULTS]")
    print(metrics)