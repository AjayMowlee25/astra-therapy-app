# backend/utils/high_quality_tts.py

from TTS.api import TTS
import numpy as np
import io
import soundfile as sf
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

# Cache the TTS model
_xtts_model = None

def get_xtts_model():
    """
    Initializes and returns the high-quality XTTS model.
    """
    global _xtts_model
    if _xtts_model is None:
        logger.info("Loading high-quality XTTS model... (This will take 2-3 minutes)")
        
        # Using XTTS which provides ElevenLabs-like quality
        _xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
        
        logger.info("High-quality XTTS model loaded!")
    return _xtts_model

def text_to_speech_high_quality(text: str, language: str = "en") -> bytes:
    """
    Converts text to high-quality speech using XTTS.
    
    Args:
        text: The text to convert to speech
        language: Language code (en, es, fr, etc.)
    
    Returns:
        Audio data in WAV format as bytes
    """
    try:
        tts = get_xtts_model()
        
        # Generate speech with high quality settings
        logger.info(f"Generating high-quality speech for: '{text}'")
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            # Generate speech with natural sounding parameters
            tts.tts_to_file(
                text=text,
                file_path=tmp_file.name,
                speaker_wav=None,  # Use default voice
                language=language,
                # Parameters for natural speech
                speed=1.0,    # Normal speed
                emotion="neutral",  # Calm, neutral emotion for therapy
                temperature=0.7,   # Controls voice variation
            )
            
            # Read back as bytes
            with open(tmp_file.name, "rb") as f:
                wav_bytes = f.read()
        
        # Clean up
        os.unlink(tmp_file.name)
        
        logger.info(f"Generated high-quality audio: {len(wav_bytes)} bytes")
        return wav_bytes
        
    except Exception as e:
        logger.error(f"Error in high-quality TTS generation: {e}")
        # Fallback to basic TTS if high-quality fails
        return text_to_speech_basic(text)

def text_to_speech_basic(text: str) -> bytes:
    """
    Fallback basic TTS if high-quality fails.
    """
    try:
        from TTS.api import TTS as BasicTTS
        basic_tts = BasicTTS("tts_models/en/ljspeech/tacotron2-DDC_ph").to("cpu")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            basic_tts.tts_to_file(text=text, file_path=tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                wav_bytes = f.read()
        os.unlink(tmp_file.name)
        return wav_bytes
    except:
        return b""