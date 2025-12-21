from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.note_segmentation import frames_to_notes
from backend.services.monophonic.validation.validate_tempo import validate_tempo
from backend.services.monophonic.pitch_extraction import extract_pitch

if __name__ == "__main__":
    audio_file = "mono6.mp3"

    # 1. Preprocess audio
    y, sr = preprocess_audio(audio_file, instrument="flute")

    # 2. Extract pitch frames
    t, f0, conf = extract_pitch(y, sr)

    # 3. Convert frames → notes  ✅ FIXED
    notes = frames_to_notes(t, f0, conf)

    # 4. Validate tempo
    metrics = validate_tempo(audio_file, notes)

    print("\n[TEMPO VALIDATION RESULTS]")
    print(f"Decision: {metrics['decision']}")
    print(f"Final Tempo: {metrics['final_tempo']}")
    print(f"Confidence: {metrics['confidence'] * 100:.1f}%")

    print("\n[DETAILS]")
    print("Audio-based:", metrics["audio_based_tempo"])
    print("Note-based:", metrics["note_based_tempo"])
