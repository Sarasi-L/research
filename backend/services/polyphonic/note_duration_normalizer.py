# backend/services/polyphonic/note_duration_normalizer.py

import pretty_midi
import numpy as np

# Expanded grid with all standard durations
DURATION_GRID_BEATS = [
    0.125,  # 32nd note
    0.25,   # 16th note
    0.375,  # dotted 16th
    0.5,    # 8th note
    0.75,   # dotted 8th
    1.0,    # quarter note
    1.5,    # dotted quarter
    2.0,    # half note
    3.0,    # dotted half
    4.0,    # whole note
    6.0,    # dotted whole
    8.0     # double whole
]

# Tuplet detection threshold
TUPLE_TOLERANCE = 0.15  # 15% deviation from grid suggests tuplet


def nearest_duration(value_in_seconds: float, beat_duration_seconds: float) -> tuple:
    
    duration_in_beats = value_in_seconds / beat_duration_seconds
    
    # Find closest grid value
    closest_beat = min(DURATION_GRID_BEATS, key=lambda x: abs(x - duration_in_beats))
    closest_seconds = closest_beat * beat_duration_seconds
    
    # Check if it's close enough to snap
    deviation = abs(duration_in_beats - closest_beat) / closest_beat if closest_beat > 0 else 1.0
    
    if deviation < 0.05:  # Within 5% - snap to grid
        return closest_seconds, False
    elif deviation < TUPLE_TOLERANCE:  # Within tuplet tolerance
        return value_in_seconds, True  # Preserve as tuplet
    else:
        return value_in_seconds, False  # Preserve original


def normalize_note_durations(input_midi: str, output_midi: str, tempo_bpm: float = None):
    
    print("\n[NORMALIZE] ===== Normalizing Note Durations =====")
    
    midi = pretty_midi.PrettyMIDI(input_midi)
    
    # Resolve tempo
    if tempo_bpm is None:
        _, tempos = midi.get_tempo_changes()
        tempo_bpm = float(tempos[0]) if len(tempos) > 0 else 120.0
        print(f"[NORMALIZE] Tempo read from MIDI: {tempo_bpm:.2f} BPM")
    else:
        print(f"[NORMALIZE] Using provided tempo: {tempo_bpm:.2f} BPM")
    
    beat_duration_seconds = 60.0 / tempo_bpm
    print(f"[NORMALIZE] Beat duration: {beat_duration_seconds:.4f}s")
    
    # Statistics
    snapped_count = 0
    preserved_count = 0
    tuplet_count = 0
    total_notes = 0
    
    for inst in midi.instruments:
        for note in inst.notes:
            total_notes += 1
            duration = note.end - note.start
            
            if duration <= 0.0:
                continue
            
            original_duration = duration
            new_duration, is_tuplet = nearest_duration(duration, beat_duration_seconds)
            
            if is_tuplet:
                tuplet_count += 1
                preserved_count += 1
            elif abs(new_duration - original_duration) / original_duration < 0.01:
                # Already close to standard
                preserved_count += 1
            else:
                # Snap to grid
                note.end = note.start + new_duration
                snapped_count += 1
    
    print(f"[NORMALIZE] Notes processed: {total_notes}")
    print(f"[NORMALIZE] Snapped to grid: {snapped_count} ({snapped_count/total_notes*100:.1f}%)")
    print(f"[NORMALIZE] Preserved (original): {preserved_count} ({preserved_count/total_notes*100:.1f}%)")
    print(f"[NORMALIZE] Detected as tuplets: {tuplet_count} ({tuplet_count/total_notes*100:.1f}%)")
    
    midi.write(output_midi)
    print(f"[NORMALIZE] ✓ Duration-normalized MIDI saved: {output_midi}")
    
    return output_midi