#backend/services/detect_monophonic_yamnet.py

from services.models.yamnet_detector import YAMNetDetector

# Load YAMNet ONCE (important for speed)
yamnet = YAMNetDetector(model_path="../models/yamnet")


def detect_monophonic_instrument(audio_path: str) -> dict:
    """
    Identify instrument in MONOPHONIC audio using YAMNet
    """

    results = yamnet.detect_instruments(audio_path)

    if not results:
        return {
            "instrument": "unknown",
            "confidence": 0.0,
            "category": "other",
            "source": "yamnet"
        }

    top = results[0]

    return {
        "instrument": top["instrument"],
        "confidence": float(top["confidence"]),
        "category": top["category"],
        "yamnet_class": top["yamnet_class"],
        "source": "yamnet"
    }
