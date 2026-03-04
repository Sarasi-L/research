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

# Instrument detection
from services.hybrid_detect_type import detect_type
from services.detect_monophonic_instrument import detect_single_instrument
from services.detect_instruments import detect_all_instruments
from services.polyphonic.separate_demucs import separate_polyphonic


router = APIRouter()

UPLOAD_DIR = Path("uploads")
STEMS_DIR = Path("stems")
MUSICXML_DIR = Path("musicxml")

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

        # ✅ Normalize note field for frontend display
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

        return JSONResponse({
            "instrument": instrument_data,
            "tempo": final_tempo,
            "key": key_result,
            "beats_per_measure": beats_per_measure,
            "musicxml_file": f"/musicxml/{musicxml_file.name}",

            # 🔽 ADD THESE TWO LINES
            "pitch_curve": pitch_result["pitch_points"],
            "note_segments": named_notes
        })


    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/analyze/polyphonic/")
async def analyze_polyphonic(filename: str):
    file_path = UPLOAD_DIR / filename

    stem_paths = separate_polyphonic(str(file_path), output_dir=str(STEMS_DIR))
    instruments = detect_all_instruments(stem_paths)

    return JSONResponse({
        "stems": {
            name: f"/stems/{Path(path).name}"
            for name, path in stem_paths.items()
        },
        "instruments": instruments
    })



@router.get("/musicxml/{filename}")
async def download_musicxml(filename: str):
    file_path = MUSICXML_DIR / filename
    if file_path.exists():
        return FileResponse(
            file_path,
            media_type="application/vnd.recordare.musicxml+xml",
            filename=filename
        )
    raise HTTPException(status_code=404, detail="MusicXML file not found")
