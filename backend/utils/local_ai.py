# backend/utils/local_ai.py

import ollama
import logging
import os

logger = logging.getLogger(__name__)

# Use Docker service name for Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

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

def get_ai_response(user_message: str, conversation_history: list = None) -> str:
    """
    Get response from local Ollama model.
    """
    try:
        # Configure Ollama client to use Docker service
        client = ollama.Client(host=OLLAMA_HOST)
        
        # Build the messages array
        messages = []
        
        # Add system prompt
        messages.append({"role": "system", "content": THERAPY_SYSTEM_PROMPT})
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        logger.info("Sending request to local Ollama model...")
        
        # Get response from Ollama
        response = client.chat(
            model="phi3",
            messages=messages,
            options={
                "temperature": 0.7,
                "num_predict": 150,
            }
        )
        
        ai_response = response['message']['content']
        logger.info(f"Local AI Response: {ai_response}")
        return ai_response
        
    except Exception as e:
        logger.error(f"Error getting local AI response: {e}")
        # Fallback response
        return "I'm here to listen. Could you tell me more about how you're feeling?"