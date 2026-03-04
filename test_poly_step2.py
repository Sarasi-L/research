from backend.services.polyphonic.voice_separation import separate_voices

# Example polyphonic audio
audio_file = "mix7 poly.mp3"

# Run voice separation
voices = separate_voices(audio_file)

print("\nTOTAL VOICES:", len(voices))
for v in voices:
    print(f"Voice: {v['voice_name']}, Duration: {len(v['audio'])/v['sr']:.2f}s, File: {v['file_path']}")
