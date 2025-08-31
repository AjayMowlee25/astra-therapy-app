# backend/utils/tts_generator.py

from TTS.api import TTS
import numpy as np
import io
import soundfile as sf
import tempfile
import os

# Cache the TTS model
_tts_model = None

def get_tts_model():
    """
    Initializes and returns the TTS model.
    """
    global _tts_model
    if _tts_model is None:
        print("Loading TTS model... (This may take a moment)")
        # Using a fast and high-quality English voice model
        # You can explore other models: https://tts.readthedocs.io/en/latest/models.html
        _tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC_ph")
        print("TTS model loaded!")
    return _tts_model

def text_to_speech(text: str) -> bytes:
    """
    Converts text to speech audio bytes.
    
    Args:
        text: The text to convert to speech
    
    Returns:
        Audio data in WAV format as bytes
    """
    try:
        tts = get_tts_model()
        
        # Generate speech as numpy array
        print(f"Generating speech for: '{text}'")
        audio_array = tts.tts(text=text)
        
        # Convert numpy array to WAV bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            # Save as WAV file
            sf.write(tmp_file.name, audio_array, 22050)  # 22.05 kHz sample rate
            # Read back as bytes
            with open(tmp_file.name, "rb") as f:
                wav_bytes = f.read()
        
        # Clean up
        os.unlink(tmp_file.name)
        
        print(f"Generated audio: {len(wav_bytes)} bytes")
        return wav_bytes
        
    except Exception as e:
        print(f"Error in TTS generation: {e}")
        # Return empty bytes if TTS fails
        return b""