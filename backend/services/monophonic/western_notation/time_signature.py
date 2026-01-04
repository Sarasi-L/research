# backend/services/monophonic/western_notation/time_signature.py

def estimate_time_signature(notes, tempo):
    """
    Estimate time signature for monophonic Western notation.

    Design decision:
    ----------------
    For monophonic audio-to-score transcription,
    time-signature inference is unreliable and not
    central to pitch/rhythm correctness.

    Therefore, we lock the output to 4/4,
    which is standard practice in AMT literature.
    """
    return "4/4"
