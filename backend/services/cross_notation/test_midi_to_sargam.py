# backend/services/cross_notation/test_midi_to_sargam.py

import pretty_midi
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from cross_notation.midi_to_sargam import midi_to_sargam, sargam_string

def test_midi_to_sargam_mapping():
   
    EXPECTED_MAP = {
        0: "Sa",   # C
        2: "Re",   # D
        4: "Ga",   # E
        5: "Ma",   # F
        7: "Pa",   # G
        9: "Dha",  # A
        11: "Ni"   # B
    }
    
    print("\n" + "="*60)
    print("MIDI TO SARGAM MAPPING TEST")
    print("="*60)
    

    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)
    

    test_pitches = {
        60: "Sa",   # C4
        62: "Re",   # D4
        64: "Ga",   # E4
        65: "Ma",   # F4
        67: "Pa",   # G4
        69: "Dha",  # A4
        71: "Ni"    # B4
    }
    
    start_time = 0.0
    for pitch, expected_sargam in test_pitches.items():
        note = pretty_midi.Note(
            velocity=100,
            pitch=pitch,
            start=start_time,
            end=start_time + 0.5
        )
        instrument.notes.append(note)
        start_time += 0.5
    
    midi.instruments.append(instrument)
    
    # Save test MIDI in current directory
    test_file = "test_sargam.mid"
    midi.write(test_file)
    print(f"\n✓ Created test MIDI file: {os.path.abspath(test_file)}")
    
    # Convert to Sargam
    sargam_notes = midi_to_sargam(test_file)
    sargam_text = sargam_string(sargam_notes)
    
    print(f"\nGenerated Sargam: {sargam_text}")
    print(f"Expected Sargam:  Sa Re Ga Ma Pa Dha Ni")
    
    # Verify each note
    print("\nDetailed Verification:")
    print("-" * 60)
    for i, (pitch, expected) in enumerate(test_pitches.items()):
        actual = sargam_notes[i]['note']
        pitch_class = pitch % 12
        status = "okay" if actual == expected else "no"
        
        print(f"{status} Pitch {pitch} (class {pitch_class:2d}) -> "
              f"Expected: {expected:4s} | Got: {actual:4s}")
    
    # Check for missing mappings
    print("\n" + "="*60)
    print("CHECKING FOR MISSING PITCH CLASSES")
    print("="*60)
    
    # Test chromatic scale (all 12 pitch classes)
    midi_chromatic = pretty_midi.PrettyMIDI()
    inst_chromatic = pretty_midi.Instrument(program=0)
    
    for pitch_class in range(12):
        pitch = 60 + pitch_class  # C4 to B4
        note = pretty_midi.Note(
            velocity=100,
            pitch=pitch,
            start=pitch_class * 0.5,
            end=(pitch_class + 1) * 0.5
        )
        inst_chromatic.notes.append(note)
    
    midi_chromatic.instruments.append(inst_chromatic)
    chromatic_file = "test_chromatic.mid"
    midi_chromatic.write(chromatic_file)
    print(f" Created chromatic test MIDI file: {os.path.abspath(chromatic_file)}")
    
    chromatic_sargam = midi_to_sargam(chromatic_file)
    
    print("\nChromatic Scale Test:")
    print("-" * 60)
    for i, note in enumerate(chromatic_sargam):
        pitch_class = i % 12
        sargam = note['note']
        
        if sargam:
            print(f"Pitch class {pitch_class:2d}: {sargam}")
        else:
            print(f"Pitch class {pitch_class:2d}:   NOT MAPPED (chromatic note)")
    
    return sargam_text == "Sa Re Ga Ma Pa Dha Ni"


def analyze_midi_sargam_coverage(midi_path):
    """
    Analyze a MIDI file and show Sargam coverage
    """
    
    # Convert to absolute path
    if not os.path.isabs(midi_path):
        # Try relative to current script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(script_dir, '../..'))
        abs_path = os.path.join(backend_dir, midi_path)
    else:
        abs_path = midi_path
    
    print("\n" + "="*60)
    print(f"ANALYZING: {midi_path}")
    print(f"Full path: {abs_path}")
    print("="*60)
    
    if not os.path.exists(abs_path):
        print(f"\n  File not found: {abs_path}")
        print("\nSearching for MIDI files in common locations...")
        
        # Search in common directories
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(script_dir, '../..'))
        
        search_paths = [
            os.path.join(backend_dir, 'musicxml', 'poly_work', 'normalized.mid'),
            os.path.join(backend_dir, 'musicxml', 'normalized.mid'),
            os.path.join(backend_dir, 'musicxml', 'poly_work', '*.mid'),
        ]
        
        found_files = []
        for search_path in search_paths:
            if '*' in search_path:
                # Glob pattern
                import glob
                found = glob.glob(search_path)
                found_files.extend(found)
            elif os.path.exists(search_path):
                found_files.append(search_path)
        
        if found_files:
            print(f"\n✓ Found {len(found_files)} MIDI file(s):")
            for f in found_files:
                print(f"  - {f}")
            
            if found_files:
                abs_path = found_files[0]
                print(f"\n→ Using: {abs_path}")
        else:
            print("\n✗ No MIDI files found. Please run the polyphonic pipeline first.")
            return None
    
    try:
        midi = pretty_midi.PrettyMIDI(abs_path)
        sargam_notes = midi_to_sargam(abs_path)
        sargam_text = sargam_string(sargam_notes)
        
        # Count pitch classes
        pitch_class_count = {}
        for inst in midi.instruments:
            for note in inst.notes:
                pc = note.pitch % 12
                pitch_class_count[pc] = pitch_class_count.get(pc, 0) + 1
        
        print("\nPitch Class Distribution:")
        print("-" * 60)
        
        SARGAM_MAP = {
                        0:"Sa",
                        1:"komal Re",
                        2:"Re",
                        3:"komal Ga",
                        4:"Ga",
                        5:"Ma",
                        6:"Tivra Ma",
                        7:"Pa",
                        8:"komal Dha",
                        9:"Dha",
                        10:"komal Ni",
                        11:"Ni"
                        }
        
        for pc in sorted(pitch_class_count.keys()):
            count = pitch_class_count[pc]
            sargam = SARGAM_MAP.get(pc, "—")
            note_name = pretty_midi.note_number_to_name(60 + pc)[:-1]  # Remove octave
            
            status = "okay" if pc in SARGAM_MAP else "no "
            
            print(f"{status} Pitch class {pc:2d} ({note_name:3s}): "
                  f"{count:4d} notes -> Sargam: {sargam:4s}")
        
        print(f"\nGenerated Sargam String:")
        print("-" * 60)
        # Print first 200 characters
        if len(sargam_text) > 200:
            print(sargam_text[:200] + "...")
            print(f"\n(Total length: {len(sargam_text)} characters)")
        else:
            print(sargam_text)
        print("-" * 60)
        
        # Calculate coverage
        total_notes = sum(pitch_class_count.values())
        mapped_notes = sum(count for pc, count in pitch_class_count.items() 
                          if pc in SARGAM_MAP)
        coverage = (mapped_notes / total_notes * 100) if total_notes > 0 else 0
        
        print(f"\nCoverage Statistics:")
        print(f"  Total notes: {total_notes}")
        print(f"  Mapped to Sargam: {mapped_notes} ({coverage:.1f}%)")
        print(f"  Unmapped (chromatic): {total_notes - mapped_notes} ({100-coverage:.1f}%)")
        
        # Save to file
        output_file = abs_path.replace('.mid', '_sargam.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"SARGAM NOTATION\n")
            f.write(f"Source MIDI: {abs_path}\n")
            f.write(f"Total notes: {total_notes}\n")
            f.write(f"Mapped: {mapped_notes} ({coverage:.1f}%)\n")
            f.write(f"\n{'-'*60}\n\n")
            f.write(sargam_text)
        
        print(f"\n✓ Sargam notation saved to: {output_file}")
        
        return sargam_notes
    
    except Exception as e:
        print(f"\n✗ Error analyzing MIDI file: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_sargam_timing(midi_path):
    """
    Verify that Sargam timing matches MIDI note timing
    """
    
    # Convert to absolute path
    if not os.path.isabs(midi_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.abspath(os.path.join(script_dir, '../..'))
        abs_path = os.path.join(backend_dir, midi_path)
    else:
        abs_path = midi_path
    
    if not os.path.exists(abs_path):
        print(f"\n  File not found for timing verification: {abs_path}")
        return
    
    print("\n" + "="*60)
    print("TIMING VERIFICATION")
    print("="*60)
    
    try:
        midi = pretty_midi.PrettyMIDI(abs_path)
        sargam_notes = midi_to_sargam(abs_path)
        
        # Get all MIDI notes
        all_midi_notes = []
        for inst in midi.instruments:
            for note in inst.notes:
                all_midi_notes.append({
                    'start': note.start,
                    'end': note.end,
                    'pitch': note.pitch,
                    'pitch_class': note.pitch % 12
                })
        
        all_midi_notes.sort(key=lambda x: x['start'])
        
        print(f"\nTotal MIDI notes: {len(all_midi_notes)}")
        print(f"Total Sargam notes: {len(sargam_notes)}")
        
        # Compare first 10 notes
        print("\nFirst 10 notes comparison:")
        print("-" * 60)
        
        SARGAM_MAP = {0:"Sa", 2:"Re", 4:"Ga", 5:"Ma", 7:"Pa", 9:"Dha", 11:"Ni"}
        
        for i in range(min(10, len(all_midi_notes), len(sargam_notes))):
            midi_note = all_midi_notes[i]
            sargam_note = sargam_notes[i]
            
            expected_sargam = SARGAM_MAP.get(midi_note['pitch_class'], "—")
            actual_sargam = sargam_note['note']
            
            timing_match = (
                abs(sargam_note['start'] - midi_note['start']) < 0.01 and
                abs(sargam_note['end'] - midi_note['end']) < 0.01
            )
            
            status = "✓" if (timing_match and actual_sargam == expected_sargam) else "✗"
            
            print(f"{status} Note {i+1}:")
            print(f"   MIDI:   {midi_note['start']:.2f}s - {midi_note['end']:.2f}s, "
                  f"pitch {midi_note['pitch']} (class {midi_note['pitch_class']:2d})")
            print(f"   Sargam: {sargam_note['start']:.2f}s - {sargam_note['end']:.2f}s, "
                  f"note '{actual_sargam}' (expected '{expected_sargam}')")
    
    except Exception as e:
        print(f"\n✗ Error in timing verification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SARGAM NOTATION VERIFICATION TEST SUITE")
    print("="*70)
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {os.path.abspath(__file__)}")
    
    # Run basic mapping test
    print("\n[TEST 1] Basic MIDI to Sargam Mapping")
    print("="*70)
    success = test_midi_to_sargam_mapping()
    print(f"\n{'✓' if success else '✗'} Basic mapping test: "
          f"{'PASSED' if success else 'FAILED'}")
    
    # Analyze your generated MIDI file
    print("\n\n[TEST 2] Analyze Generated MIDI File")
    print("="*70)
    
    # Try multiple possible paths
    midi_paths = [
        "musicxml/poly_work/normalized.mid",
        "../../musicxml/poly_work/normalized.mid",
        os.path.join(os.path.dirname(__file__), '../../musicxml/poly_work/normalized.mid'),
    ]
    
    analyzed = False
    for midi_file in midi_paths:
        result = analyze_midi_sargam_coverage(midi_file)
        if result is not None:
            analyzed = True
            
            print("\n\n[TEST 3] Timing Verification")
            print("="*70)
            verify_sargam_timing(midi_file)
            break
    
    if not analyzed:
        print("\n  Could not find normalized.mid file")
        print("\nTo generate the file, run:")
        print("  1. Upload an audio file through the web interface")
        print("  2. Run the polyphonic analysis pipeline")
        print("  3. The file will be created at: backend/musicxml/poly_work/normalized.mid")
    
    print("\n\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)