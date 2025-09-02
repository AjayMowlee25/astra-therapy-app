# backend/utils/groq_ai.py
import os
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# System prompt for the therapy assistant
THERAPY_SYSTEM_PROMPT = """You are Astra, a compassionate, empathetic, and mindful listener. 
You are not a therapist but a supportive friend. Your goal is to validate the user's feelings, 
help them feel heard, and gently guide them towards self-reflection. 

Keep your responses:
- Short and conversational (1-2 sentences)
- Warm and empathetic
- Focused on validation and support
- Never clinical or diagnostic

Respond as if you are in a real-time conversation."""

def get_ai_response(user_message: str, conversation_history: List[Dict] = None) -> str:
    """
    Get response from Groq API using direct HTTP requests
    """
    try:
        # Build messages array - Groq expects specific format
        messages = [{"role": "system", "content": THERAPY_SYSTEM_PROMPT}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        logger.info("Sending request to Groq API...")
        
        # Make direct HTTP request to Groq API - CORRECTED FORMAT
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gemma2-9b-it",
                "messages": messages,
                "max_tokens": 150,
                "temperature": 0.7
                # Removed "stream": False as it might cause issues
            },
            timeout=30
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        ai_response = data["choices"][0]["message"]["content"]
        
        logger.info(f"Groq Response: {ai_response}")
        return ai_response
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return "I'm having trouble connecting to the AI service. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        return "I'm having connection issues. Please check your internet and try again."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "I'm here to listen. Could you tell me more about how you're feeling?"