# backend/test_yamnet.py
from pathlib import Path
from backend.services.models.yamnet_detector import YAMNetDetector

# Path to local YAMNet SavedModel
model_path = Path(__file__).resolve().parents[1] / "models" / "yamnet"

# Initialize detector
detector = YAMNetDetector(model_path=str(model_path))
print("✓ YAMNet loaded successfully!\n")

# Test audio file
audio_file = "mix7.mp3"

print("=== STEP 1: All Top Predictions ===")
all_predictions = detector.get_top_predictions(audio_file, top_n=50)
for pred in all_predictions[:30]:
    print(f"{pred['class']:40s} mean: {pred['mean_confidence']*100:5.2f}% | max: {pred['max_confidence']*100:5.2f}%")

print("\n=== STEP 2: Instrument Detection (Segment Analysis) ===")
instruments = detector.detect_instruments(audio_file)

print(f"\n=== FINAL DETECTED INSTRUMENTS ===")
if instruments:
    for r in instruments:
        print(f"\n• {r['instrument'].upper()}")
        print(f"  Confidence: {r['confidence']*100:.1f}%")
        print(f"  Max: {r['max_confidence']*100:.1f}% | Mean: {r['mean_confidence']*100:.1f}%")
        print(f"  Present in {r['segments_detected']}/{r['total_segments']} segments")
        print(f"  Category: {r['category']}")
        print(f"  YAMNet class: {r['yamnet_class']}")
else:
    print("No instruments detected with sufficient confidence")
    print("\nTIP: YAMNet may struggle with:")
    print("  - Electronic/synthesized music (no clear acoustic instruments)")
    print("  - Heavily processed vocals")
    print("  - Dense polyphonic mixes")
    print("\nTry:")
    print("  1. Using isolated stems (drums, bass, other)")
    print("  2. Audio with clear acoustic instruments")
    print("  3. Rely on Rule-Based detector for electronic music")