import os

MIDI_FOLDER = r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\Essen Folksong Database"

OUTPUT_FOLDER = r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\Essen Folksong Database\audio_output"

SOUNDFONT_PATH = r"D:\My Documents\SLIIT\DS4.1\Research Project\multi_notation_generator_\FluidR3_GM.sf2"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print("MIDI folder exists:", os.path.exists(MIDI_FOLDER))
print("SoundFont exists:", os.path.exists(SOUNDFONT_PATH))

files = [f for f in os.listdir(MIDI_FOLDER) if f.endswith((".mid", ".midi"))]
print("Total MIDI files found:", len(files))

for file in files:
    midi_path = os.path.join(MIDI_FOLDER, file)
    wav_path = os.path.join(OUTPUT_FOLDER, file.replace(".mid", ".wav"))

    command = f'fluidsynth -ni -F "{wav_path}" -r 44100 "{SOUNDFONT_PATH}" "{midi_path}"'
    
    print(f"\n🎵 Converting: {file}")
    os.system(command)

    if os.path.exists(wav_path):
        print(f"✅ Created: {wav_path}")
    else:
        print(f"❌ Failed: {file}")