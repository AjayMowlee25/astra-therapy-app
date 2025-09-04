# backend/utils/groq_tts.py
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def text_to_speech(text: str, voice: str = "Ruby-PlayAI") -> bytes:
    """
    Converts text to speech using Groq's TTS API.
    Returns audio bytes (WAV format).
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY not set")
            return b""

        logger.info(f"Generating Groq TTS for: '{text[:50]}...'")
        
        # Groq TTS API endpoint
        url = "https://api.groq.com/openai/v1/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "playai-tts",
            "input": text,
            "voice": voice,  # Use one of the approved voices
            "response_format": "wav"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            audio_bytes = response.content
            logger.info(f"Groq TTS generated {len(audio_bytes)} bytes")
            return audio_bytes
        else:
            logger.error(f"Groq TTS API error: {response.status_code} - {response.text}")
            return b""
            
    except Exception as e:
        logger.error(f"Groq TTS error: {e}")
        return b""  # Graceful fallback