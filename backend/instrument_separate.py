from pathlib import Path
from demucs.pretrained import get_model
from demucs.separate import main as demucs_separate
import sys

def separate_instruments(input_file: str, output_dir: str):
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Input audio: {input_file}")

        model = get_model(name="htdemucs")
        print("[INFO] HTDemucs model loaded on CPU.")

        # Full 4-stem separation (NO --two-stems)
        demucs_separate([
            "--out", str(output_dir),
            str(input_file)
        ])

        print("[SUCCESS] Separation complete. Check output folder for stems.")

    except Exception as e:
        print(f"[ERROR] Separation failed: {e}")

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    separate_instruments(input_file, output_dir)
