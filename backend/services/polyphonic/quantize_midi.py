# backend/services/polyphonic/quantize_midi.py

import pretty_midi
import numpy as np
from pathlib import Path


def build_tempo_grid(tempo_bpm: float, total_duration: float, subdivision: int = 8):
    
    seconds_per_beat = 60.0 / tempo_bpm
    seconds_per_subdivision = seconds_per_beat / subdivision

    grid = np.arange(0.0, total_duration + seconds_per_subdivision, seconds_per_subdivision)
    return grid


def find_nearest_grid(time: float, grid: np.ndarray) -> float:
    idx = np.argmin(np.abs(grid - time))
    return float(grid[idx])


def quantize_to_grid(input_midi: str, beat_times: np.ndarray, output_path: str,
                     subdivision: int = 8, tempo_bpm: float = None):
    

    midi = pretty_midi.PrettyMIDI(input_midi)

    
    total_duration = midi.get_end_time() + 2.0  # +2s padding

    if tempo_bpm is not None:
        
        grid = build_tempo_grid(tempo_bpm, total_duration, subdivision)
        print(f"[QUANTIZE] Using tempo-based grid: {tempo_bpm:.2f} BPM, "
              f"subdivision={subdivision}, step={60.0/tempo_bpm/subdivision:.4f}s")
    else:
        
        from backend.services.polyphonic.quantize_midi import _build_beat_grid
        grid = _build_beat_grid(beat_times, subdivision)
        print(f"[QUANTIZE] WARNING: Using irregular beat-time grid (tempo_bpm not provided)")

    seconds_per_beat = 60.0 / tempo_bpm if tempo_bpm else None
    max_note_duration = (seconds_per_beat * 3.0) if seconds_per_beat else 2.0

    quantized_count = 0
    for inst in midi.instruments:
        for note in inst.notes:
            note.start = find_nearest_grid(note.start, grid)
            note.end = find_nearest_grid(note.end, grid)

            if note.end <= note.start:
                note.end = note.start + (60.0 / tempo_bpm / subdivision if tempo_bpm else 0.05)

            duration = note.end - note.start
            if duration > max_note_duration:
                note.end = note.start + max_note_duration

            quantized_count += 1

    midi.write(str(output_path))
    print(f"[QUANTIZE] ✓ Quantized {quantized_count} notes → {output_path}")
    return str(output_path)


def _build_beat_grid(beat_times: np.ndarray, subdivision: int) -> np.ndarray:
    
    grid = []
    for i in range(len(beat_times) - 1):
        start = beat_times[i]
        end = beat_times[i + 1]
        step = (end - start) / subdivision
        for s in range(subdivision):
            grid.append(start + s * step)
    grid.append(beat_times[-1])
    return np.array(grid)