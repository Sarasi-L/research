from backend.services.monophonic.note_quantization import quantize_duration
from validation.note_quantization_validation.test_quantization_rules import TEST_CASES

correct = 0

print("\n===== NOTE QUANTIZATION RULE VALIDATION =====\n")

for dur, expected in TEST_CASES:
    pred = quantize_duration(dur)
    status = "✔" if pred == expected else "✘"

    print(f"Input: {dur:.2f} beats | Expected: {expected:15s} "
          f"| Predicted: {pred:15s} {status}")

    if pred == expected:
        correct += 1

accuracy = (correct / len(TEST_CASES)) * 100

print("\n--------------------------------------------")
print(f"Test cases : {len(TEST_CASES)}")
print(f"Accuracy   : {accuracy:.2f}%")
