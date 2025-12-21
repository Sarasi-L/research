from backend.services.monophonic.note_naming import apply_key_aware_naming
from backend.services.monophonic.note_quantization import quantize_notes
from backend.services.monophonic.validation.validate_tempo import validate_tempo
from backend.services.monophonic.validation.key_validation import validate_key
from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes

if __name__ == "__main__":
    audio_file = "mono6.mp3"

    # Preprocess
    y, sr = preprocess_audio(audio_file, instrument="organ")

    # Pitch extraction
    t, f0, conf = extract_pitch(y, sr)

    # Notes
    notes = frames_to_notes(t, f0, conf)

    # Tempo
    tempo_metrics = validate_tempo(audio_file, notes)
    tempo = tempo_metrics["final_tempo"]

    # Quantize
    quantized = quantize_notes(notes, tempo)

    # Key detection
    key_metrics = validate_key(notes)
    key = key_metrics["key"]

    # 🔑 Key-aware note naming
    named_notes = apply_key_aware_naming(quantized, key)

    print("\n[KEY-AWARE NOTES]")
    for i, n in enumerate(named_notes, 1):
        print(
            f"{i:02d}. {n['note_name']} | "
            f"{n['duration_name']} | "
            f"{n['duration_beats']} beats"
        )
