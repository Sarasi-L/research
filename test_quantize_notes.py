# test_quantize_notes.py

from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes
from backend.services.monophonic.validation.validate_tempo import validate_tempo
from backend.services.monophonic.note_quantization import quantize_notes


if __name__ == "__main__":
    audio_file = "mix7.mp3"
    instrument = "flute"

    # 1. Preprocess audio
    y, sr = preprocess_audio(audio_file, instrument=instrument)

    # 2. Extract pitch
    t, f0, conf = extract_pitch(y, sr)

    # 3. Frames → note events
    notes = frames_to_notes(t, f0, conf)

    print(f"\n[INFO] Detected {len(notes)} notes")

    # 4. Validate tempo (reuse existing system)
    tempo_metrics = validate_tempo(audio_file, notes)

    print("\n[TEMPO VALIDATION]")
    print(f"Decision: {tempo_metrics['decision']}")
    print(f"Final Tempo: {tempo_metrics['final_tempo']} BPM")
    print(f"Confidence: {tempo_metrics['confidence'] * 100:.1f}%")

    if tempo_metrics["decision"] != "ACCEPTED":
        print("\n❌ Tempo rejected — cannot quantize notes reliably")
        exit(1)

    tempo = tempo_metrics["final_tempo"]

    # 5. NOTE-LEVEL QUANTIZATION  ✅ NEW STEP
    quantized_notes = quantize_notes(notes, tempo)

    # 6. Print quantized results
    print("\n[QUANTIZED NOTES]")
    for i, n in enumerate(quantized_notes):
        print(
            f"{i+1:02d}. "
            f"Pitch={n['pitch']} Hz | "
            f"Duration={n['duration_beats']} beats → "
            f"{n['duration_name']}"
        )
