from utils.cloud_stt import speech_to_text
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import base64
from dotenv import load_dotenv
import os
from utils.cloud_tts import text_to_speech
from utils.groq_ai import get_ai_response

# Load environment variables from .env file
load_dotenv()

# Initialize App
app = FastAPI(title="Astra Therapy API", version="0.1.0")

# Configure CORS (Cross-Origin Resource Sharing)
# Allow all origins for Docker deployment
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://astra-frontend-ka2s.onrender.com",  # ← ADD THIS
    "https://astra-backend-4phc.onrender.com",   # ← ADD THIS
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_forwarded_for_header(request, call_next):
    # This is crucial for WebSockets on Render to get the correct client IP
    if "x-forwarded-for" in request.headers:
        # If behind a proxy, use the original host for URL generation
        request.scope["headers"].append((
            b"x-forwarded-for",
            request.headers["x-forwarded-for"].encode()
        ))
    response = await call_next(request)
    return response

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
            user_text = speech_to_text(data)

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

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "astra-backend"}

# Keep the root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Hello from Astra Therapy Backend! Local AI edition."}

# # The main function to run the server using Uvicorn.
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)