# backend/routers/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import shutil
import traceback
import numpy as np

# Monophonic utilities
from services.monophonic.run_monophonic_pipeline import run_monophonic_pipeline
from services.monophonic.note_segmentation import (
    frames_to_notes,
    smooth_note_durations
)
from services.monophonic.tempo_beat_estimation import estimate_tempo_and_beats
from services.monophonic.note_based_tempo import estimate_tempo_from_notes
from services.monophonic.tempo_selector import select_final_tempo
from services.monophonic.note_quantization import quantize_notes
from services.monophonic.key_detection import detect_key
from services.monophonic.note_naming import apply_key_aware_naming

# Western notation utilities
from services.monophonic.western_notation.time_signature import estimate_time_signature
from services.monophonic.western_notation.measure_grouping import group_notes_into_measures
from services.monophonic.western_notation.ties_rests import apply_ties_and_rests
from services.monophonic.western_notation.musicxml_export import generate_musicxml

from services.monophonic.sargam_converter import convert_xml_to_sargam

from services.monophonic.direct_midi_export import create_midi_from_quantized_notes

# Instrument detection
from services.hybrid_detect_type import detect_type
from services.detect_monophonic_instrument import detect_single_instrument
from services.detect_instruments import detect_all_instruments
from services.polyphonic.separate_demucs import separate_polyphonic


from services.polyphonic.detect_piano_from_stems import detect_piano_from_stems
from services.polyphonic.run_piano_pipeline import run_piano_pipeline

from services.polyphonic.run_polyphonic_pipeline import run_polyphonic_pipeline


router = APIRouter()

UPLOAD_DIR = Path("uploads")
STEMS_DIR = Path("stems")
MUSICXML_DIR = Path("musicxml")
MIDI_DIR = Path("musicxml")  # 

UPLOAD_DIR.mkdir(exist_ok=True)
STEMS_DIR.mkdir(exist_ok=True)
MUSICXML_DIR.mkdir(exist_ok=True)


@router.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    try:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        audio_type, confidence = detect_type(str(file_path))

        return JSONResponse({
            "message": "Audio uploaded and analyzed",
            "filename": file.filename,
            "audio_file": f"/uploads/{file.filename}",
            "type": audio_type,
            "confidence": float(confidence)
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/monophonic/")
async def analyze_monophonic(filename: str):
    try:
        file_path = UPLOAD_DIR / filename

        instrument_data = detect_single_instrument(str(file_path))
        instrument_name = instrument_data.get("instrument", "unknown")

        pitch_result = run_monophonic_pipeline(
            str(file_path), instrument_name
        )

        times = [p["time"] for p in pitch_result["pitch_points"]]
        freqs = [p["frequency"] for p in pitch_result["pitch_points"]]
        confs = [p["confidence"] for p in pitch_result["pitch_points"]]

        note_segments = frames_to_notes(times, freqs, confs, instrument=instrument_name)
        note_segments = smooth_note_durations(note_segments)

        audio_tempo = estimate_tempo_and_beats(str(file_path))
        note_tempo = estimate_tempo_from_notes(note_segments)
        final_tempo = select_final_tempo(audio_tempo, note_tempo)

        quantized_notes = quantize_notes(note_segments, final_tempo["tempo"])
        key_result = detect_key(quantized_notes)

        if key_result is None or key_result.get("confidence", 0) < 0.3:
            key_result = {"key": "C", "mode": "major", "confidence": 0.0}

        named_notes = apply_key_aware_naming(
            quantized_notes, f"{key_result['key']} {key_result['mode']}"
        )

        
        direct_midi_file = MUSICXML_DIR / f"{filename}_direct.mid"

        create_midi_from_quantized_notes(
            notes=named_notes,
            tempo_bpm=final_tempo["tempo"],
            output_file=str(direct_midi_file)
        )

        # Normalize note field for frontend display
        for n in named_notes:
            if n.get("is_rest", False):
                n["note"] = "Rest"
            else:
                n["note"] = n.get("note_name", None)


        beats_per_measure = int(
            estimate_time_signature(named_notes, final_tempo["tempo"]).split("/")[0]
        )

        measures = group_notes_into_measures(named_notes, beats_per_measure)
        measures = apply_ties_and_rests(measures, beats_per_measure)

        musicxml_file = MUSICXML_DIR / f"{filename}.musicxml"
        generate_musicxml(
            western_measures=measures,
            tempo_bpm=final_tempo["tempo"],
            key_name=f"{key_result['key']} {key_result['mode']}",
            beats_per_measure=beats_per_measure,
            output_file=str(musicxml_file)
        )

        # Convert MusicXML to Sargam
        sargam_output = convert_xml_to_sargam(
            xml_path=str(musicxml_file),
            key=key_result["key"],
            beats_per_measure=beats_per_measure
        )

        print("\n[SARGAM OUTPUT]")
        print(sargam_output["sargam_text"])

        return JSONResponse({
            "instrument": instrument_data,
            "tempo": final_tempo,
            "key": key_result,
            "beats_per_measure": beats_per_measure,
            "musicxml_file": f"/musicxml/{musicxml_file.name}",
            "midi_direct": f"/musicxml/{direct_midi_file.name}",


            
            "pitch_curve": pitch_result["pitch_points"],
            "note_segments": named_notes,

            "sargam_notation": sargam_output["sargam_text"]
        })


    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/polyphonic/")
async def analyze_polyphonic(filename: str):
    try:
        file_path = UPLOAD_DIR / filename

       
        # STEP 1 — Demucs separation
        stem_paths = separate_polyphonic(
            str(file_path),
            output_dir=str(STEMS_DIR)
        )

        # STEP 2 — Instrument detection
        instruments = detect_all_instruments(stem_paths)

       
        piano_only = detect_piano_from_stems(stem_paths)

        musicxml_file = None

        

        if piano_only:

            print("\n[PIPELINE] Running PIANO pipeline")

            pipeline_result = run_piano_pipeline(
                str(file_path),
                output_dir=str(MUSICXML_DIR)
            )

        else:

            print("\n[PIPELINE] Running MULTI-INSTRUMENT pipeline")

            pipeline_result = run_polyphonic_pipeline(
                str(file_path),
                output_dir=str(MUSICXML_DIR)
            )

        musicxml_file = f"/musicxml/{Path(pipeline_result['xml']).name}"
        
        
        midi_file = "/midi/normalized"  
        
        sargam = pipeline_result["sargam"]

        print(f"\n✅ Generated files:")
        print(f"   MusicXML: {musicxml_file}")
        print(f"   MIDI: {midi_file} (normalized.mid)")


        # STEP 5 — Return result
        return JSONResponse({
            "piano_only": piano_only,
            "stems": {
                name: f"/stems/{Path(path).name}"
                for name, path in stem_paths.items()
            },
            "instruments": instruments,
            "musicxml_file": musicxml_file,
            "midi_file": midi_file,
            "sargam_notation": sargam
        })

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Universal file server for musicxml directory and subdirectories
@router.get("/musicxml/{path:path}")
async def serve_musicxml_files(path: str):
    """
    Serve MusicXML and MIDI files from the musicxml directory and subdirectories
    """
    file_path = MUSICXML_DIR / path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    
    # Prevent directory traversal attacks
    try:
        file_path.resolve().relative_to(MUSICXML_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Determine media type
    if path.endswith('.musicxml') or path.endswith('.xml'):
        media_type = "application/vnd.recordare.musicxml+xml"
    elif path.endswith('.mid') or path.endswith('.midi'):
        media_type = "audio/midi"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=file_path.name
    )


@router.get("/midi/normalized")
async def get_normalized_midi():
    """
    Serve the always-normalized MIDI file:
    backend/musicxml/poly_work/normalized.mid
    """
    normalized_path = MUSICXML_DIR / "poly_work" / "normalized.mid"

    if not normalized_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Normalized MIDI file not found"
        )

    return FileResponse(
        normalized_path,
        media_type="audio/midi",
        filename="normalized.mid"
    )