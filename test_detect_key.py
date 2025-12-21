from backend.services.monophonic.preprocess_audio import preprocess_audio
from backend.services.monophonic.pitch_extraction import extract_pitch
from backend.services.monophonic.note_segmentation import frames_to_notes
from backend.services.monophonic.note_quantization import quantize_notes
from backend.services.monophonic.key_detection import detect_key

audio_file = "mix7.mp3"

y, sr = preprocess_audio(audio_file, instrument="flute")
t, f0, conf = extract_pitch(y, sr)
notes = frames_to_notes(t, f0, conf)

tempo = 178.21  # use accepted tempo
quantized = quantize_notes(notes, tempo)

key_info = detect_key(quantized)

print("\n[KEY DETECTION]")
print(f"Key: {key_info['key']} {key_info['mode']}")
print(f"Confidence: {key_info['confidence']}")
