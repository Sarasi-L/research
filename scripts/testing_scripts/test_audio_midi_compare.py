from backend.services.validation.audio_midi_compare import compare_audio_midi

compare_audio_midi("mix3poly.mp3",
                   "backend/midi_output/full_song_key_ts.mid")