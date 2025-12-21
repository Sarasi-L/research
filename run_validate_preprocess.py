from backend.services.monophonic.validation.validate_preprocess import validate_preprocessing

result = validate_preprocessing(
    "mix7.mp3",
    "flute"
)

print(result)
