# backend/utils/cloud_stt.py
import os
import tempfile
import logging
import groq
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize the Groq client
client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

def speech_to_text(audio_bytes: bytes) -> str:
    """
    Transcribes audio bytes to text using Groq's Whisper API.
    """
    try:
        if not os.getenv("GROQ_API_KEY"):
            logger.error("GROQ_API_KEY not set.")
            return ""

        logger.info("Transcribing audio with Groq Whisper API...")
        
        # Create a temporary file for the audio bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name

        try:
            # Open the temporary file and send it to Groq
            with open(tmp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",  # Specify Groq's Whisper model
                    response_format="text",    # Get plain text directly
                    language="en"              # Optional: for accuracy
                )
            # Since we use response_format="text", transcript is a string
            return transcript
        finally:
            # Clean up the temporary file
            os.unlink(tmp_file_path)

    except Exception as e:
        logger.error(f"Error in Groq speech-to-text: {e}")
        return ""