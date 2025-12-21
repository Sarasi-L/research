def select_final_tempo(audio_tempo: dict, note_tempo: dict) -> dict:
    """
    Decide final tempo for monophonic Western notation
    """

    # 1️⃣ Prefer note-based tempo (symbolic, stable)
    if (
        note_tempo
        and note_tempo.get("tempo") is not None
        and note_tempo.get("confidence", 0) >= 0.6
    ):
        return {
            "tempo": note_tempo["tempo"],
            "confidence": note_tempo["confidence"],
            "source": "note_based"
        }

    # 2️⃣ Fallback to beat-based tempo
    if audio_tempo and audio_tempo.get("tempo") is not None:
        return {
            "tempo": audio_tempo["tempo"],
            "confidence": 0.6,
            "source": "beat_based"
        }

    # 3️⃣ Absolute fallback
    return {
        "tempo": 120.0,
        "confidence": 0.3,
        "source": "default"
    }
