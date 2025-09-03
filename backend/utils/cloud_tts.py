# backend/utils/cloud_tts.py
import os
from elevenlabs import generate, play, set_api_key, save
import requests
import logging
from dotenv import load_dotenv

load_dotenv()  # Load environment variables (for local dev)

logger = logging.getLogger(__name__)
# Configure ElevenLabs API Key (set this in Render's environment variables)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
set_api_key(ELEVENLABS_API_KEY)

def text_to_speech(text: str, voice: str = "Rachel") -> bytes:
    """
    Converts text to speech using ElevenLabs API.
    Returns audio bytes (WAV format).
    """
    try:
        if not ELEVENLABS_API_KEY:
            logger.error("ELEVENLABS_API_KEY not set.")
            return b""

        logger.info(f"Generating ElevenLabs speech: '{text}'")

        # Generate audio bytes directly from the API
        audio = generate(
            text=text,
            voice=voice, # You can use "Rachel", "Domi", "Bella", "Antoni", etc.
            model="eleven_monolingual_v1"
        )

        logger.info(f"Generated audio: {len(audio)} bytes")
        return audio

    except Exception as e:
        logger.error(f"Error in ElevenLabs TTS generation: {e}")
        return b""