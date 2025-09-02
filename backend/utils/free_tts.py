# backend/utils/free_tts.py
from TTS.api import TTS
import numpy as np
import soundfile as sf
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

# Cache the TTS model
_tts_model = None

def get_tts_model():
    """
    Initializes TTS model without license prompts.
    """
    global _tts_model
    if _tts_model is None:
        logger.info("Loading free TTS model...")
        
        # Use a model that doesn't require license acceptance
        # These models are completely free and open source
        model_options = [
            "tts_models/en/ljspeech/tacotron2-DDC",  # Good quality
            "tts_models/en/ljspeech/glow-tts",       # Very natural
            "tts_models/en/vctk/vits",               # Multiple voices
            "tts_models/en/ek1/tacotron2"           # Alternative
        ]
        
        # Try models in order until one works
        for model_name in model_options:
            try:
                _tts_model = TTS(model_name).to("cpu")
                logger.info(f"Loaded TTS model: {model_name}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {model_name}: {e}")
                continue
        
        if _tts_model is None:
            raise Exception("Could not load any TTS model")
            
        logger.info("TTS model loaded successfully!")
    return _tts_model

def text_to_speech(text: str, voice: str = "default") -> bytes:
    """
    Converts text to speech with human-like quality.
    """
    try:
        tts = get_tts_model()
        
        logger.info(f"Generating speech: '{text}'")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            # Generate speech with natural parameters
            tts.tts_to_file(
                text=text,
                file_path=tmp_file.name,
                # Parameters for natural speech
                speed=0.9,    # Slightly slower for more natural sound
                emotion="neutral",
            )
            
            # Read back as bytes
            with open(tmp_file.name, "rb") as f:
                wav_bytes = f.read()
        
        # Clean up
        os.unlink(tmp_file.name)
        
        logger.info(f"Generated audio: {len(wav_bytes)} bytes")
        return wav_bytes
        
    except Exception as e:
        logger.error(f"Error in TTS generation: {e}")
        return b""