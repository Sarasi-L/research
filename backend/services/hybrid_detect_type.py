# backend/services/hybrid_detect_type.py

from services.detect_type_crepe import detect_type as crepe_detect
from services.detect_type_crnn import detect_type as crnn_detect

def detect_type(audio_path: str):
  
    # STEP 1: CREPE analysis
    crepe_type, crepe_conf = crepe_detect(audio_path)
    print(f"[HYBRID] CREPE - {crepe_type} ({crepe_conf:.2f})")

    # STEP 2: CRNN analysis 
    crnn_type, crnn_conf = crnn_detect(audio_path)
    print(f"[HYBRID] CRNN - {crnn_type} ({crnn_conf:.2f})")

    # STEP 3: Strong agreement
    if crepe_type == crnn_type:
        return crepe_type, round((crepe_conf + crnn_conf) / 2, 3)

    # STEP 4: Strong CREPE mono override
    if crepe_type == "monophonic" and crepe_conf >= 0.75:
        return "monophonic", crepe_conf

    # STEP 5: CREPE-dominant (physics trusted)
    if crepe_conf >= 0.85 and crnn_conf < 0.90:
        return crepe_type, crepe_conf

    # STEP 6: CRNN-dominant
    if crnn_conf >= 0.90 and crepe_conf < 0.70:
        return crnn_type, crnn_conf

    # STEP 7: Borderline expressive mono
    if crepe_type == "monophonic" and crnn_type == "polyphonic":
        return "monophonic", round((crepe_conf + (1 - crnn_conf)) / 2, 3)

    # STEP 8: Fallback
    return crnn_type, crnn_conf
