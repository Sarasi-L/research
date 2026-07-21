from backend.services.polyphonic.multipitch_detection import detect_multipitch

audio_path = "mono6.mp3"

notes = detect_multipitch(audio_path)

print("\nTOTAL NOTES:", len(notes))
