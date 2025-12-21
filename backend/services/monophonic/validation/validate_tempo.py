from backend.services.monophonic.tempo_beat_estimation import estimate_tempo_and_beats
from backend.services.monophonic.note_based_tempo import estimate_tempo_from_notes
from backend.services.monophonic.tempo_selector import select_final_tempo


def validate_tempo(audio_path, notes):
    """
    Validate tempo for monophonic transcription
    """

    audio_tempo = estimate_tempo_and_beats(audio_path)
    note_tempo = estimate_tempo_from_notes(notes)

    final = select_final_tempo(audio_tempo, note_tempo)

    decision = "ACCEPTED" if final["confidence"] >= 0.5 else "REJECTED"

    return {
        "decision": decision,
        "final_tempo": final["tempo"],
        "confidence": round(final["confidence"], 3),
        "source": final["source"],
        "audio_based_tempo": audio_tempo,
        "note_based_tempo": note_tempo
    }
