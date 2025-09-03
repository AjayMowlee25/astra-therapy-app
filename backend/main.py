import traceback
import logging
import time
import os

# Set up basic logging to see errors clearly
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    logger.info("Starting import of dependencies...")
    
    # Import core dependencies first
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    import json
    import asyncio
    import base64
    from dotenv import load_dotenv
    
    logger.info("Core dependencies imported successfully")
    
    # Now import your utility modules with individual try-catch
    try:
        from utils.cloud_stt import speech_to_text
        logger.info("cloud_stt imported successfully")
    except Exception as e:
        logger.error(f"Failed to import cloud_stt: {e}")
        raise
    
    try:
        from utils.cloud_tts import text_to_speech
        logger.info("cloud_tts imported successfully")
    except Exception as e:
        logger.error(f"Failed to import cloud_tts: {e}")
        raise
    
    try:
        from utils.groq_ai import get_ai_response
        logger.info("groq_ai imported successfully")
    except Exception as e:
        logger.error(f"Failed to import groq_ai: {e}")
        raise

    # Load environment variables from .env file
    logger.info("Loading environment variables...")
    load_dotenv()

    # Initialize App
    logger.info("Creating FastAPI app...")
    app = FastAPI(title="Astra Therapy API", version="0.1.0")

    # Configure CORS (Cross-Origin Resource Sharing)
    origins = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://astra-frontend-ka2s.onrender.com",
        "https://astra-backend-4phc.onrender.com",
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
        if "x-forwarded-for" in request.headers:
            request.scope["headers"].append((
                b"x-forwarded-for",
                request.headers["x-forwarded-for"].encode()
            ))
        response = await call_next(request)
        return response

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        try:
            await websocket.accept()
            logger.info("Client connected via WebSocket")
            
            # Test if API keys are available immediately
            groq_key = os.getenv("GROQ_API_KEY")
            elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
            
            logger.info(f"GROQ_API_KEY available: {bool(groq_key)}")
            logger.info(f"ELEVENLABS_API_KEY available: {bool(elevenlabs_key)}")
            
            if not groq_key:
                error_msg = "ERROR: GROQ_API_KEY not set in environment variables"
                logger.error(error_msg)
                await websocket.send_text(error_msg)
                return
                
            if not elevenlabs_key:
                error_msg = "ERROR: ELEVENLABS_API_KEY not set in environment variables"
                logger.error(error_msg)
                await websocket.send_text(error_msg)
                return
            
            conversation_history = []
            
            try:
                while True:
                    data = await websocket.receive_bytes()
                    logger.info(f"Received audio data, length: {len(data)} bytes")

                    user_text = speech_to_text(data)
                    logger.info(f"Transcribed text: {user_text}")

                    crisis_keywords = ['kill myself', 'want to die', 'end it all', 'suicide']
                    if any(keyword in user_text.lower() for keyword in crisis_keywords):
                        crisis_response = "I hear that you're in immense pain, and that worries me. Your safety is the most important thing. Please, right now, reach out to a human professional at the National Suicide Prevention Lifeline by calling or texting 988. I am here with you."
                        await websocket.send_text(f"CRISIS_RESPONSE:{crisis_response}")
                        continue

                    logger.info("Sending request to Groq AI...")
                    ai_text_response = get_ai_response(user_text, conversation_history)
                    
                    conversation_history.append({"role": "user", "content": user_text})
                    conversation_history.append({"role": "assistant", "content": ai_text_response})
                    
                    if len(conversation_history) > 8:
                        conversation_history = conversation_history[-8:]

                    logger.info(f"AI Response: {ai_text_response}")

                    logger.info("Generating speech with ElevenLabs...")
                    audio_bytes = text_to_speech(ai_text_response)
                    
                    if audio_bytes:
                        response_data = {
                            "text": ai_text_response,
                            "audio": base64.b64encode(audio_bytes).decode('utf-8')
                        }
                        await websocket.send_json(response_data)
                        logger.info("Sent text and audio response to client")
                    else:
                        await websocket.send_text(f"AI_RESPONSE:{ai_text_response}")

            except WebSocketDisconnect:
                logger.info("Client disconnected")
            except Exception as e:
                logger.error(f"Error in WebSocket communication: {e}")
                logger.error(traceback.format_exc())
                await websocket.send_text(f"ERROR: {str(e)}")

        except Exception as e:
            logger.error(f"WebSocket endpoint setup failed: {e}")
            logger.error(traceback.format_exc())
            raise

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "astra-backend"}

    @app.get("/test-keys")
    async def test_keys():
        """Endpoint to check if API keys are properly set"""
        return {
            "groq_available": bool(os.getenv("GROQ_API_KEY")),
            "elevenlabs_available": bool(os.getenv("ELEVENLABS_API_KEY")),
            "message": "Check Render environment variables"
        }

    @app.get("/test-apis")
    async def test_apis():
        """Test if the external APIs are actually working"""
        try:
            # Test Groq API
            from utils.groq_ai import get_ai_response
            groq_test = get_ai_response("Hello, are you working?", [])
            
            # Test ElevenLabs TTS
            from utils.cloud_tts import text_to_speech  
            tts_test = text_to_speech("Test message")
            
            return {
                "groq_working": bool(groq_test),
                "tts_working": bool(tts_test),
                "groq_response": groq_test[:100] + "..." if groq_test else None,
                "tts_bytes": len(tts_test) if tts_test else 0
            }
            
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    @app.get("/")
    async def root():
        return {"message": "Hello from Astra Therapy Backend! Local AI edition."}

    logger.info("FastAPI app setup completed successfully!")
    logger.info("Server is ready to run...")

except Exception as e:
    logger.error(f"CRITICAL ERROR during application startup: {e}")
    logger.error(traceback.format_exc())
    logger.info("Waiting 5 minutes before exit to allow log viewing...")
    time.sleep(300)
    raise