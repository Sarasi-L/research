from backend.services.monophonic.validation.key_validation import (
    build_pitch_class_histogram,
    print_pitch_class_histogram,
    validate_key_with_histogram
)

# This comes from YOUR quantization output
quantized_notes = [
    {"pitch": 498.16},
    {"pitch": 436.99},
    {"pitch": 423.64},
    {"pitch": 376.01},
    {"pitch": 319.27},
    {"pitch": 642.24},
    {"pitch": 357.01},
]


# 1️⃣ Extract pitches
note_pitches_hz = [n["pitch"] for n in quantized_notes]

# 2️⃣ Build pitch-class histogram
histogram = build_pitch_class_histogram(note_pitches_hz)

# 3️⃣ Print histogram (for debugging / UI)
print_pitch_class_histogram(histogram)

# 4️⃣ Validate detected key (from your ML model)
detected_key = "D# minor"   # example output from your key detector

result = validate_key_with_histogram(
    histogram=histogram,
    detected_key=detected_key
)

print("\n[KEY VALIDATION RESULT]")
for k, v in result.items():
    print(f"{k}: {v}")
