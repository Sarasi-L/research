# backend/services/detect_monophonic_instrument.py
"""
Detect instrument in monophonic audio using YAMNet
Only runs after CREPE confirms it's monophonic
"""

from services.models.yamnet_detector import YAMNetDetector

def detect_single_instrument(audio_path: str) -> dict:
    """
    Use YAMNet to identify the instrument in monophonic audio
    
    Args:
        audio_path: Path to the monophonic audio file
        
    Returns:
        dict with instrument details from YAMNet
    """
    print("[INFO] Running YAMNet for monophonic instrument detection...")
    
    try:
        # Initialize YAMNet detector
        detector = YAMNetDetector(confidence_threshold=0.001)
        
        # Detect instruments using YAMNet in MONOPHONIC MODE
        detections = detector.detect_instruments(audio_path, monophonic_mode=True)
        
        if not detections:
            print("[WARNING] YAMNet found no instruments, using fallback")
            return {
                "instrument": "unknown",
                "confidence": 0.5,
                "category": "other",
                "source": "fallback",
                "yamnet_class": "Unknown",
                "characteristics": "Could not identify specific instrument"
            }
        
        # Get the top detection
        top_instrument = detections[0]
        
        print(f"[INFO] YAMNet detected: {top_instrument['instrument']} "
              f"({top_instrument['confidence']*100:.1f}% confidence)")
        print(f"[DEBUG] YAMNet class: {top_instrument['yamnet_class']}")
        print(f"[DEBUG] Max confidence: {top_instrument['max_confidence']:.3f}, "
              f"Mean: {top_instrument['mean_confidence']:.3f}")
        print(f"[DEBUG] Segments detected: {top_instrument['segments_detected']}/{top_instrument['total_segments']}")
        
        # Add characteristics based on instrument type
        characteristics = _get_instrument_characteristics(top_instrument['instrument'])
        top_instrument['characteristics'] = characteristics
        
        # If confidence is very low, warn user
        if top_instrument['confidence'] < 0.15:
            top_instrument['characteristics'] = (
                "⚠️ Low confidence detection. " + characteristics
            )
        
        return top_instrument
        
    except Exception as e:
        print(f"[ERROR] YAMNet detection failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "instrument": "unknown",
            "confidence": 0.5,
            "category": "other",
            "source": "error",
            "yamnet_class": "Error",
            "characteristics": f"Detection failed: {str(e)}"
        }


def _get_instrument_characteristics(instrument: str) -> str:
    """
    Get human-readable characteristics for each instrument
    """
    characteristics = {
        # Strings
        'guitar': 'String instrument with frets, typically 6 strings',
        'bass_guitar': 'Low-pitched string instrument, typically 4 strings',
        'violin': 'Bowed string instrument, highest pitch in violin family',
        'cello': 'Large bowed string instrument, rich low tones',
        'viola': 'Bowed string instrument, between violin and cello',
        'double_bass': 'Largest bowed string instrument, very low pitch',
        'harp': 'Plucked string instrument with triangular frame',
        'banjo': 'String instrument with circular drum-like body',
        'ukulele': 'Small 4-string guitar-like instrument',
        'mandolin': 'Small string instrument with 4 pairs of strings',
        'sitar': 'Indian string instrument with resonating strings',
        
        # Keyboards
        'piano': 'Keyboard instrument with hammers striking strings',
        'electric_piano': 'Electronic version of piano',
        'organ': 'Keyboard instrument with pipes or electronic tone generation',
        'harpsichord': 'Keyboard instrument with plucked strings',
        'synthesizer': 'Electronic keyboard with various sound generation',
        'keyboard': 'Generic keyboard instrument',
        
        # Percussion
        'drums': 'Percussion instruments played with sticks or hands',
        'percussion': 'Instruments struck to produce sound',
        'bongo': 'Pair of small hand drums',
        'conga': 'Tall narrow drum played with hands',
        'tabla': 'Pair of Indian hand drums',
        'tambourine': 'Hand-held drum with metal jingles',
        'marimba': 'Wooden bar percussion with resonators',
        'xylophone': 'Wooden bar percussion instrument',
        'vibraphone': 'Metal bar percussion with motor-driven resonators',
        'glockenspiel': 'Metal bar percussion with bright tone',
        'steelpan': 'Caribbean percussion made from steel drums',
        'timpani': 'Large kettle drums',
        
        # Brass
        'trumpet': 'Brass instrument with valves, bright tone',
        'trombone': 'Brass instrument with slide mechanism',
        'french_horn': 'Coiled brass instrument with mellow tone',
        'tuba': 'Largest brass instrument, very low pitch',
        'saxophone': 'Single-reed woodwind/brass instrument',
        'brass_instrument': 'Metal wind instrument',
        
        # Woodwinds
        'flute': 'Woodwind instrument with air blown across hole',
        'clarinet': 'Single-reed woodwind instrument',
        'oboe': 'Double-reed woodwind with penetrating tone',
        'bassoon': 'Large double-reed woodwind, low pitch',
        'piccolo': 'Small flute with very high pitch',
        'recorder': 'Simple woodwind with whistle mouthpiece',
        'bagpipes': 'Reed instrument with air bag and drones',
        'harmonica': 'Small mouth-blown reed instrument',
        
        # Other
        'accordion': 'Bellows-driven reed instrument with keyboard',
        'theremin': 'Electronic instrument played without touch',
        'music_box': 'Mechanical instrument with tuned metal comb',
    }
    
    return characteristics.get(instrument, 'Musical instrument detected')