# backend/utils/audio_processor.py

from faster_whisper import WhisperModel
import tempfile
import os
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache the model
_whisper_model = None

def get_whisper_model():
    """
    Initializes and returns the faster-whisper model.
    """
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading faster-whisper model... (This may take a moment)")
        # Use CPU for compatibility, but you can use "cuda" if you have a GPU
        # "int8" compute type is efficient for CPU usage
        _whisper_model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",
            download_root="./models"  # Optional: specify download directory
        )
        logger.info("faster-whisper model loaded!")
    return _whisper_model

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Converts raw audio bytes to text using faster-whisper.
    
    Args:
        audio_bytes: Raw audio data in bytes (e.g., from WebSocket)
    
    Returns:
        Transcribed text as a string
    """
    tmp_path = None
    try:
        model = get_whisper_model()
        
        # Save to temporary file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        logger.info(f"Transcribing audio file: {tmp_path}")
        
        # Transcribe using faster-whisper with optimized settings
        segments, info = model.transcribe(
            tmp_path,
            language="en",        # Specify English for better accuracy
            beam_size=5,          # Balance between speed and accuracy
            vad_filter=True,      # Voice activity detection to remove silence
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )
        
        logger.info(f"Detected language: {info.language}, probability: {info.language_probability}")
        
        # Combine all segments into a single transcription
        transcription = " ".join(segment.text for segment in segments).strip()
        
        if not transcription:
            transcription = "[I didn't catch that. Could you please repeat?]"
        
        logger.info(f"Transcription: '{transcription}'")
        return transcription
        
    except Exception as e:
        logger.error(f"Error in transcription: {e}")
        # Return a friendly error message if transcription fails
        return "[Sorry, I couldn't understand the audio. Please try again.]"
    
    finally:
        # Always clean up the temporary file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug("Temporary file cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Could not delete temp file {tmp_path}: {cleanup_error}")

# Optional: If you need array processing later, you can add this function back
# with proper numpy import



def transcribe_audio_array(audio_array: np.ndarray, sample_rate: int = 16000) -> str:
    
    try:
        model = get_whisper_model()
        
        # Transcribe directly from numpy array
        segments, info = model.transcribe(
            audio_array,
            language="en",
            beam_size=5,
            vad_filter=True,
            sample_rate=sample_rate
        )
        
        transcription = " ".join(segment.text for segment in segments).strip()
        logger.info(f"Array transcription: '{transcription}'")
        return transcription
        
    except Exception as e:
        logger.error(f"Error in array transcription: {e}")
        return "[Audio processing error]"
