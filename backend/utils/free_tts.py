# backend/utils/free_tts.py
import requests
import logging
import re

logger = logging.getLogger(__name__)

def text_to_speech(text: str) -> bytes:
    """
    Free TTS using Google's public TTS API.
    Returns audio bytes (MP3 format).
    """
    try:
        # Clean and truncate text for URL safety
        cleaned_text = re.sub(r'[^\w\s.,!?;-]', '', text)[:200]
        
        if not cleaned_text.strip():
            return b""
            
        logger.info(f"Generating free TTS for: '{cleaned_text}...'")
        
        # Use Google's free TTS API
        response = requests.get(
            "https://translate.google.com/translate_tts",
            params={
                'ie': 'UTF-8',
                'q': cleaned_text,
                'tl': 'en',  # English language
                'client': 'tw-ob',  # Text-to-speech client
                'total': '1',
                'idx': '0'
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Free TTS generated {len(response.content)} bytes")
            return response.content
        else:
            logger.warning(f"Free TTS API failed with status: {response.status_code}")
            return b""
            
    except Exception as e:
        logger.error(f"Free TTS error: {e}")
        return b""  # Silent fallback to avoid crashing