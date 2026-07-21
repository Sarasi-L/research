from backend.services.monophonic.western_notation.time_signature import estimate_time_signature

# Sample note data
test_notes = [
    {"start": 0.0}, {"start": 0.5}, {"start": 1.0}, {"start": 1.5},
    {"start": 2.0}, {"start": 2.5}, {"start": 3.0}, {"start": 3.5}
]
tempo = 120  # BPM

ts = estimate_time_signature(test_notes, tempo)
print("Estimated Time Signature:", ts)
# ✅ Expected: 4/4
