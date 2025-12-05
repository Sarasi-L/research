from pathlib import Path
import torch
import torchaudio
import soundfile as sf
import os

def separate_instruments(input_file: str, output_root: str):
    try:
        print(f"[INFO] Input audio: {input_file}")

        # -------------------------------
        # Get song name (without extension)
        # -------------------------------
        song_name = Path(input_file).stem
        output_dir = Path(output_root) / song_name
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Output directory: {output_dir}")

        # Load local model
        model_path = "models/htdemucs/htdemucs.th"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        print("[INFO] Loading HTDemucs from local file...")

        from demucs.pretrained import get_model
        from demucs.apply import apply_model

        # Load model architecture
        model = get_model("htdemucs")
        state = torch.load(model_path, map_location="cpu")
        model.load_state_dict(state)
        model.eval()

        # Load audio using torchaudio
        wav, sr = torchaudio.load(input_file)

        # Resample if needed
        if sr != model.samplerate:
            print(f"[INFO] Resampling {sr} → {model.samplerate}")
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=model.samplerate)
            wav = resampler(wav)

        wav = wav.unsqueeze(0)

        # Run separation
        print("[INFO] Running separation...")
        stems = apply_model(model, wav)

        # Save stems
        names = model.sources
        for i, name in enumerate(names):
            out_path = output_dir / f"{name}.wav"
            sf.write(out_path, stems[0, i].cpu().numpy().T, model.samplerate)

        print(f"[SUCCESS] Separation complete! Stored in: {output_dir}")

    except Exception as e:
        print(f"[ERROR] Separation failed: {e}")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_root = sys.argv[2]
    separate_instruments(input_file, output_root)
