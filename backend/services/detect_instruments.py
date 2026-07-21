# backend/services/detect_instruments.py

from typing import List, Dict
from pathlib import Path

from services.models.yamnet_detector import YAMNetDetector
from services.models.rule_based_detector import RuleBasedDetector
from services.models.ensemble_detector import EnsembleDetector

# Global detector instance (loaded once)
_ensemble_detector = None

def get_ensemble_detector():
    
    global _ensemble_detector
    
    if _ensemble_detector is None:
        print("[INFO] Initializing ensemble detector...")
        
        _ensemble_detector = EnsembleDetector()
        
        try:
            yamnet_path = Path(__file__).parent.parent / "models" / "yamnet"
            
            if yamnet_path.exists():
                yamnet = YAMNetDetector(model_path=str(yamnet_path))
                _ensemble_detector.add_detector(yamnet, weight=1.2)  
                print("[INFO] YAMNet detector loaded (local model)")
            else:
                print("[WARNING] YAMNet model not found locally")
                print("[INFO] Run 'python save_yamnet.py' to download YAMNet model")
                yamnet = YAMNetDetector()  # Load from TF Hub
                _ensemble_detector.add_detector(yamnet, weight=1.2)
                print("[INFO] YAMNet detector loaded (from TF Hub)")
                
        except Exception as e:
            print(f"[WARNING] Could not load YAMNet: {e}")
            print("[INFO] Continuing with Rule-Based detector only")
        
        try:
            rule_based = RuleBasedDetector()
            _ensemble_detector.add_detector(rule_based, weight=1.0)
            print("[INFO] Rule-based detector loaded")
        except Exception as e:
            print(f"[ERROR] Could not load rule-based detector: {e}")
        
        print("[INFO] Ensemble detector ready!")
    
    return _ensemble_detector


class InstrumentDetector:
    
    def __init__(self):
        self.ensemble = get_ensemble_detector()
    
    def detect_instruments_in_stem(self, audio_path: str, stem_name: str) -> List[Dict]:
        
        print(f"[INFO] Analyzing {stem_name} stem for instruments...")
        
        if stem_name == "other":
            return self._detect_melodic_instruments(audio_path)
        elif stem_name == "drums":
            return self._analyze_drums(audio_path)
        elif stem_name == "bass":
            return self._analyze_bass(audio_path)
        elif stem_name == "vocals":
            return self._analyze_vocals(audio_path)
        else:
            return [{'instrument': stem_name, 'confidence': 0.5, 'category': 'unknown'}]
    
    def _detect_melodic_instruments(self, audio_path: str) -> List[Dict]:
        
        print("[INFO] Running ensemble detection on 'other' stem...")
        
        # Run ensemble detection (both YAMNet and Rule-Based)
        instruments = self.ensemble.detect_instruments(audio_path)
        
        filtered = []
        exclude_keywords = ['vocal', 'drum', 'bass', 'singing', 'speech', 'voice']
        
        for inst in instruments:
            instrument_name = inst['instrument'].lower()
            
            if any(keyword in instrument_name for keyword in exclude_keywords):
                print(f"[INFO] Filtered out '{inst['instrument']}' (should be in different stem)")
                continue
            
            filtered.append(inst)
        
        if not filtered:
            print("[INFO] No specific instruments detected, using generic placeholder")
            filtered.append({
                'instrument': 'melodic_instrument',
                'confidence': 0.5,
                'category': 'other',
                'characteristics': 'Unidentified melodic instrument',
                'sources': ['Generic'],
                'detectors_agreed': 0
            })
        
        
        filtered.sort(key=lambda x: x['confidence'], reverse=True)
        return filtered[:5]
    
    def _analyze_drums(self, audio_path: str) -> List[Dict]:
        """Analyze drum stem - simple fixed detection"""
        return [{
            'instrument': 'drum_kit',
            'confidence': 0.9,
            'category': 'percussion',
            'characteristics': 'Full drum kit (kick, snare, hi-hat, cymbals)',
            'components': ['kick_drum', 'snare_drum', 'hi_hat', 'cymbals', 'toms'],
            'sources': ['Demucs'],
            'detectors_agreed': 1
        }]
    
    def _analyze_bass(self, audio_path: str) -> List[Dict]:
        """Analyze bass stem - simple fixed detection"""
        return [{
            'instrument': 'bass_guitar',
            'confidence': 0.8,
            'category': 'bass',
            'characteristics': 'Low frequency bass instrument',
            'sources': ['Demucs'],
            'detectors_agreed': 1
        }]
    
    def _analyze_vocals(self, audio_path: str) -> List[Dict]:
        """Analyze vocal stem - simple fixed detection"""
        return [{
            'instrument': 'vocals',
            'confidence': 0.85,
            'category': 'vocals',
            'characteristics': 'Human voice',
            'sources': ['Demucs'],
            'detectors_agreed': 1
        }]


def detect_all_instruments(stem_paths: Dict[str, str]) -> Dict[str, List[Dict]]:
   
    detector = InstrumentDetector()
    all_instruments = {}
    
    for stem_name, stem_path in stem_paths.items():
        print(f"\n{'='*60}")
        print(f"Processing {stem_name.upper()} stem")
        print(f"{'='*60}")
        
        instruments = detector.detect_instruments_in_stem(stem_path, stem_name)
        all_instruments[stem_name] = instruments
        
        print(f"\n[RESULT] {stem_name} stem: Found {len(instruments)} instrument(s)")
        for inst in instruments:
            sources = inst.get('sources', ['Unknown'])
            detectors = inst.get('detectors_agreed', 1)
            
            print(f"  • {inst['instrument']:20s} ({inst['confidence']*100:5.1f}% confidence)")
            print(f"    Category: {inst.get('category', 'unknown'):15s}")
            print(f"    Detected by: {', '.join(sources)} ({detectors} detector(s) agreed)")
            
            if 'characteristics' in inst:
                print(f"    Info: {inst['characteristics']}")
    
    print(f"\n{'='*60}")
    print("Instrument detection complete!")
    print(f"{'='*60}\n")
    
    return all_instruments