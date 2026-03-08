import csv
import numpy as np
import pretty_midi
from pathlib import Path
from music21 import converter
import xml.etree.ElementTree as ET


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
EVAL_DIR = ROOT / "eval_outputs"
GT_XML_DIR = ROOT / "groundtruth_xml"

OUTPUT_CSV = ROOT / "evaluation_results.csv"


# MIDI tolerance (seconds)
ONSET_TOL = 0.05
OFFSET_TOL = 0.05

# XML tolerance (seconds)
XML_ONSET_TOL = 0.05


# ============================================================
# MIDI LOADER
# ============================================================

def load_midi_notes(midi_path):

    midi = pretty_midi.PrettyMIDI(str(midi_path))

    notes = []

    for inst in midi.instruments:

        if inst.is_drum:
            continue

        for n in inst.notes:

            notes.append((n.start, n.end, n.pitch, n.velocity))

    return sorted(notes, key=lambda x: (x[0], x[2]))


# ============================================================
# MIDI EVALUATION
# ============================================================

def evaluate_midi(gt_path, pred_path):

    gt = load_midi_notes(gt_path)
    pred = load_midi_notes(pred_path)

    if not gt or not pred:
        return 0,0,0,0,0

    used=set()
    tp=0
    tp_offset=0
    tp_vel=0

    for g_on,g_off,g_pitch,g_vel in gt:

        for i,(p_on,p_off,p_pitch,p_vel) in enumerate(pred):

            if i in used:
                continue

            if g_pitch==p_pitch and abs(g_on-p_on)<=ONSET_TOL:

                used.add(i)
                tp+=1

                if abs(g_off-p_off)<=OFFSET_TOL:
                    tp_offset+=1

                if abs(p_vel-g_vel)/max(g_vel,1)<=0.2:
                    tp_vel+=1

                break

    precision=tp/len(pred)
    recall=tp/len(gt)

    f1=0
    if precision+recall>0:
        f1=2*precision*recall/(precision+recall)

    offset_acc=tp_offset/tp if tp else 0
    velocity_acc=tp_vel/tp if tp else 0

    return precision,recall,f1,offset_acc,velocity_acc


# ============================================================
# XML NOTE LOADER (FIXED)
# ============================================================

def load_xml_notes(xml_path):

    score = converter.parse(str(xml_path))

    notes=[]

    flat = score.flatten()

    for n in flat.notes:

        if n.isNote:

            try:
                t = float(n.seconds)
            except:
                continue

            notes.append((t, n.pitch.midi))

        elif n.isChord:

            try:
                t = float(n.seconds)
            except:
                continue

            for c in n.notes:
                notes.append((t, c.pitch.midi))

    return sorted(notes, key=lambda x:(x[0],x[1]))


# ============================================================
# XML EVALUATION (RESEARCH STYLE)
# ============================================================

def evaluate_xml(gt_xml,pred_xml):

    gt=load_xml_notes(gt_xml)
    pred=load_xml_notes(pred_xml)

    if not gt or not pred:
        return 0,0,0

    used=set()
    matches=0

    for p_time,p_pitch in pred:

        for i,(g_time,g_pitch) in enumerate(gt):

            if i in used:
                continue

            if p_pitch==g_pitch and abs(p_time-g_time)<=XML_ONSET_TOL:

                matches+=1
                used.add(i)
                break

    precision=matches/len(pred)
    recall=matches/len(gt)

    f1=0
    if precision+recall>0:
        f1=2*precision*recall/(precision+recall)

    return precision,recall,f1


# ============================================================
# XML STRUCTURE METRICS
# ============================================================

def xml_structure(xml_path):

    root=ET.parse(str(xml_path)).getroot()

    notes=sum(
        1 for n in root.findall(".//note")
        if n.find("rest") is None
    )

    chords=sum(
        1 for n in root.findall(".//note")
        if n.find("chord") is not None
    )

    measures=len(root.findall(".//measure"))

    return notes,chords,measures


# ============================================================
# MAIN EVALUATION
# ============================================================

def run():

    songs=[d for d in EVAL_DIR.iterdir() if d.is_dir()]

    results=[]

    print(f"\nEvaluating {len(songs)} songs\n")

    for song_dir in songs:

        song=song_dir.name

        gt_midi=song_dir/"ground_truth.mid"
        norm_midi=song_dir/"normalized.mid"

        pred_xml=song_dir/"predicted.musicxml"
        gt_xml=GT_XML_DIR/f"{song}.musicxml"

        if not gt_midi.exists() or not norm_midi.exists():
            continue

        print("Processing:",song[:70])

        # MIDI
        p,r,f1,off_acc,vel_acc = evaluate_midi(gt_midi,norm_midi)

        # XML
        xp=xr=xf1=0
        notes=chords=measures=0

        if gt_xml.exists() and pred_xml.exists():

            xp,xr,xf1=evaluate_xml(gt_xml,pred_xml)

            notes,chords,measures=xml_structure(pred_xml)

        results.append({

            "song":song,

            "midi_precision":round(p,4),
            "midi_recall":round(r,4),
            "midi_f1":round(f1,4),

            "offset_accuracy":round(off_acc,4),
            "velocity_accuracy":round(vel_acc,4),

            "xml_precision":round(xp,4),
            "xml_recall":round(xr,4),
            "xml_f1":round(xf1,4),

            "pred_notes":notes,
            "pred_chords":chords,
            "pred_measures":measures
        })


    # ============================================================
    # SAVE CSV
    # ============================================================

    with open(OUTPUT_CSV,"w",newline="") as f:

        writer=csv.DictWriter(f,fieldnames=results[0].keys())
        writer.writeheader()

        for r in results:
            writer.writerow(r)


    # ============================================================
    # PRINT SUMMARY
    # ============================================================

    def avg(k):
        return round(np.mean([r[k] for r in results]),4)


    print("\n============================")
    print("AVERAGE RESULTS")
    print("============================")

    print("\nMIDI")
    print("Precision:",avg("midi_precision"))
    print("Recall   :",avg("midi_recall"))
    print("F1       :",avg("midi_f1"))

    print("\nXML")
    print("Precision:",avg("xml_precision"))
    print("Recall   :",avg("xml_recall"))
    print("F1       :",avg("xml_f1"))

    print("\nResults saved to:")
    print(OUTPUT_CSV)


# ============================================================

if __name__=="__main__":
    run()