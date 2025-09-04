# backend/test_groq_tts_final.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print(f"API Key available: {bool(api_key)}")

# Try different voices from the approved list
voices_to_test = [
    "Ruby-PlayAI",    # Female voice
    "Atlas-PlayAI",   # Male voice  
    "Jennifer-PlayAI", # Female voice
    "Mason-PlayAI"    # Male voice
]

for voice in voices_to_test:
    print(f"\nTesting voice: {voice}")
    
    url = "https://api.groq.com/openai/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "playai-tts",
        "input": f"Hello, this is a test of {voice} voice",
        "voice": voice,
        "response_format": "wav"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS with {voice}! Generated {len(response.content)} bytes")
            
            # Save the audio
            filename = f"test_{voice.lower().replace('-playai', '')}.wav"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Audio saved as '{filename}'")
            break  # Stop after first success
            
        else:
            print(f"❌ Failed: {response.text[:100]}...")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")