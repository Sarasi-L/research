import librosa
from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.validation.validate_pitch import validate_pitch

y, sr = preprocess_audio("mix7.mp3", "flute")
metrics = validate_pitch(y, sr)

print(metrics)
