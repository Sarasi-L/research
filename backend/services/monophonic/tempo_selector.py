# backend/services/monophonic/tempo_selector.py


COMMON_TEMPOS = [60, 72, 80, 84, 90, 96, 100, 108, 112, 120,
                 126, 132, 138, 144, 152, 160, 168, 176, 180, 192]


def snap_tempo(tempo, confidence=1.0):
    """
    Snap estimated tempo to nearest musically common BPM — but ONLY
    when the estimate is close to a common tempo AND confidence is high.

    FIX (CRITICAL): The old code always snapped, meaning a real tempo of
    100 BPM would be forced to 96 BPM. At 120 BPM this causes a 4% error
    on EVERY note duration, making the transcription drift out of sync.

    New rules:
    - Only snap if within 3 BPM of a common tempo (was effectively unlimited).
    - Only snap if confidence >= 0.75.
    - Otherwise trust the raw estimate (rounded to 1 decimal).
    """
    nearest = min(COMMON_TEMPOS, key=lambda t: abs(t - tempo))
    gap = abs(nearest - tempo)

    if confidence >= 0.75 and gap <= 3.0:
        return float(nearest)

    # Don't snap — round to nearest integer to keep it clean
    return float(round(tempo))


def select_final_tempo(audio_tempo: dict, note_tempo: dict) -> dict:
    """
    Decide final tempo for monophonic Western notation.

    Priority:
    1. Note-based tempo (most musically accurate) — if high confidence
    2. Audio beat-based tempo (librosa) — fallback
    3. Default 120 BPM — last resort

    FIX: Pass confidence into snap_tempo so we only snap when safe to do so.
    FIX: Lowered note_tempo confidence threshold from 0.6 → 0.45 because
         the new note_based_tempo.py produces more reliable estimates that
         may score slightly lower on regularity for expressive playing.
    """

    # 1. Prefer note-based tempo
    if (
        note_tempo
        and note_tempo.get("tempo") is not None
        and note_tempo.get("confidence", 0) >= 0.45
    ):
        raw_tempo = note_tempo["tempo"]
        conf = note_tempo["confidence"]
        snapped = snap_tempo(raw_tempo, confidence=conf)
        return {
            "tempo": snapped,
            "raw_tempo": raw_tempo,
            "confidence": conf,
            "source": "note_based",
            "snapped": snapped != raw_tempo
        }

    # 2. Fallback to beat-based tempo
    if audio_tempo and audio_tempo.get("tempo") is not None:
        raw_tempo = audio_tempo["tempo"]
        # Beat-based is less reliable, use lower confidence for snap decision
        snapped = snap_tempo(raw_tempo, confidence=0.5)
        return {
            "tempo": snapped,
            "raw_tempo": raw_tempo,
            "confidence": 0.55,
            "source": "beat_based",
            "snapped": snapped != raw_tempo
        }

    # 3. Absolute fallback
    return {
        "tempo": 120.0,
        "raw_tempo": 120.0,
        "confidence": 0.3,
        "source": "default",
        "snapped": False
    }