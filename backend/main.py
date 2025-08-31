from utils.audio_processor import transcribe_audio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
# import openai  # <-- REMOVE THIS LINE
# import google.generativeai as genai # <-- ADD THIS IMPORT
import json
import asyncio
import base64
from dotenv import load_dotenv
import os
# from utils.tts_generator import text_to_speech
from utils.high_quality_tts import text_to_speech_high_quality as text_to_speech
from utils.local_ai import get_ai_response

# Load environment variables from .env file
load_dotenv()

# Initialize App
app = FastAPI(title="Astra Therapy API", version="0.1.0")

# Configure CORS (Cross-Origin Resource Sharing)
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW GEMINI CODE ---
# Configure the Gemini client with your API key from the .env file
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# --- END NEW GEMINI CODE ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected via WebSocket")
    
    # Initialize conversation history for this session
    conversation_history = []
    
    try:
        while True:
            # 1. Wait for audio data from frontend
            data = await websocket.receive_bytes()
            print(f"Received audio data, length: {len(data)} bytes")

            # 2. Transcribe the audio
            user_text = transcribe_audio(data)

            # 3. CHECK FOR CRISIS KEYWORDS (keep this important safety check)
            crisis_keywords = ['kill myself', 'want to die', 'end it all', 'suicide']
            if any(keyword in user_text.lower() for keyword in crisis_keywords):
                crisis_response = "I hear that you're in immense pain, and that worries me. Your safety is the most important thing. Please, right now, reach out to a human professional at the National Suicide Prevention Lifeline by calling or texting 988. I am here with you."
                await websocket.send_text(f"CRISIS_RESPONSE:{crisis_response}")
                continue

            # 4. Send text to LOCAL AI (Ollama)
            print("Sending request to local AI...")
            ai_text_response = get_ai_response(user_text, conversation_history)
            
            # 5. Update conversation history (optional, for context)
            conversation_history.append({"role": "user", "content": user_text})
            conversation_history.append({"role": "assistant", "content": ai_text_response})
            
            # Keep history manageable (last 4 exchanges)
            if len(conversation_history) > 8:  # 4 user + 4 assistant messages
                conversation_history = conversation_history[-8:]

            print(f"AI Response: {ai_text_response}")

            # 6. Convert AI response to speech
            audio_bytes = text_to_speech(ai_text_response)
            
            if audio_bytes:
                # Send both text and audio back to frontend
                response_data = {
                    "text": ai_text_response,
                    "audio": base64.b64encode(audio_bytes).decode('utf-8')
                }
                await websocket.send_json(response_data)
                print("Sent text and audio response to client")
            else:
                # Fallback: send only text if TTS fails
                await websocket.send_text(f"AI_RESPONSE:{ai_text_response}")

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.send_text(f"ERROR: {str(e)}")

# Keep the root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Hello from Astra Therapy Backend! Gemini edition."}

# The main function to run the server using Uvicorn.
# This block is crucial. It tells Python to run the server when the script is executed directly.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)