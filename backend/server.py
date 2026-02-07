import os
import io
import json
import re
from google.cloud import texttospeech
import socketio
import uvicorn
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import Response, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Local Project Imports
from . import database
from . import logic
import tempfile
import subprocess
import threading
import asyncio
import urllib.parse

# Load Environment Variables
load_dotenv(".env.local")
load_dotenv(".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_3_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SILAS_VOICE = os.getenv("SILAS_VOICE", "en-GB-Studio-B")

client = genai.Client(api_key=GEMINI_API_KEY)
tts_client = texttospeech.TextToSpeechClient()

def strip_markdown(text: str) -> str:
    """Removes common markdown characters for cleaner TTS playback."""
    # Remove bold/italic markers (* and _)
    text = re.sub(r'[*_]', '', text)
    # Remove markdown headers (#)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove backticks (`)
    text = text.replace('`', '')
    # Remove dashes/bullets at start of lines
    text = re.sub(r'^\s*[-+]\s+', '', text, flags=re.MULTILINE)
    return text.strip()

# Load Silas System Prompt
# Path updated to look in prompts/ directory
PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.md")
with open(PROMPT_PATH, "r") as f:
    SILAS_PROMPT = f.read()

app = FastAPI(title="Project Silas: Thinking Hardware Agent")

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

# Mount Dashboard
# Path updated to point to dashboard/ at the root
DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard")
app.mount("/dashboard", StaticFiles(directory=DASHBOARD_PATH), name="dashboard")

# Database Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "dashboard", "index.html")
    return FileResponse(INDEX_PATH)

@app.get("/tts")
async def tts_stream(text: str):
    """Generates Silas's voice using Google Cloud TTS and streams it to the ESP32."""
    clean_text = strip_markdown(text)
    
    input_text = texttospeech.SynthesisInput(text=clean_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB", 
        name=SILAS_VOICE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    
    return Response(content=response.audio_content, media_type="audio/mpeg")
 Miranda
async def get_gemini_3_response(user_input: str, device_id: str, db: Session):
    # Retrieve session for thought signature persistence
    session_record = db.query(database.Session).filter(database.Session.device_id == device_id).first()
    previous_signature = session_record.last_thought_signature if session_record else None

    # Logic Router: Determine if Silas needs to "Think Hard"
    level = logic.determine_thinking_level(user_input)
    
    contents = []
    if previous_signature:
        # Re-insert signature to maintain context across reboots
        contents.append(types.Content(role="model", parts=[types.Part(thought_signature=previous_signature)]))
    
    contents.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

    # Generate Content with Thinking Enabled (Asynchronous)
    response = await client.aio.models.generate_content(
        model="gemini-3-flash-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=types.Content(parts=[types.Part(text=SILAS_PROMPT)]),
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_level=level
            )
        )
    )

    # --- Processing & Cleaning ---
    full_response_text = getattr(response, 'text', "") or ""
    
    # Safely get signature from the model's parts
    new_signature = None
    try:
        if response.candidates and response.candidates[0].content.parts:
            for part in reversed(response.candidates[0].content.parts):
                # Using getattr is safer than hasattr for SDK objects
                sig = getattr(part, 'thought_signature', None)
                if sig:
                    new_signature = sig
                    break
    except Exception as e:
        print(f"Signature Extraction Warning: {e}")
    
    thought_summary = getattr(response, 'thought_summary', "Analysing circuit...") or "Analysing circuit..."
    
    # Extract Thought Tokens for the hackathon "compute proof"
    usage = getattr(response, 'usage_metadata', None)
    thought_tokens = 0
    if usage:
        # Check for various possible attribute names in different SDK versions
        thought_tokens = getattr(usage, 'thought_token_count', 0) or getattr(usage, 'thought_tokens', 0)
    
    # Extract Hardware State JSON block from text
    hardware_state = {"status": "idle"}
    clean_text = full_response_text
    json_match = re.search(r"```json\n(.*?)\n```", full_response_text, re.DOTALL)
    
    if json_match:
        try:
            hardware_state = json.loads(json_match.group(1).strip())
            clean_text = re.sub(r"```json\n.*?\n```", "", full_response_text, flags=re.DOTALL).strip()
        except Exception as e:
            print(f"JSON Parse Error: {e}")

    # --- Dashboard Update (Non-blocking) ---
    asyncio.create_task(sio.emit('new_thought', {'text': thought_summary}))
    asyncio.create_task(sio.emit('thoughts', {
        'device_id': device_id,
        'level': level,
        'summary': thought_summary,
        'text': clean_text,
        'hardware_state': hardware_state,
        'thought_tokens': thought_tokens,
        'signature': new_signature
    }))

    # --- Persistence Logic ---
    if not session_record:
        session_record = database.Session(device_id=device_id, last_thought_signature=new_signature)
        db.add(session_record)
    else:
        session_record.last_thought_signature = new_signature
    
    # Save History
    db.add(database.History(device_id=device_id, role="user", content=user_input))
    db.add(database.History(device_id=device_id, role="model", content=clean_text))
    db.commit()

    return clean_text, thought_tokens, level

@app.post("/voice")
async def handle_voice(
    device_id: str = Form(...), 
    audio: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Reset dashboard UI
    await sio.emit('reset', {})
    
    audio_bytes = await audio.read()
    
    # Step 1: Transcribe Audio using multimodal capabilities (Asynchronous)
    transcribe_response = await client.aio.models.generate_content(
        model="gemini-2.0-flash", 
        contents=[
            types.Content(role="user", parts=[
                types.Part(inline_data=types.Blob(mime_type="audio/wav", data=audio_bytes)),
                types.Part(text="Transcribe this audio exactly. Just the text.")
            ])
        ]
    )
    user_text = (transcribe_response.text or "").strip()
    print(f"[{device_id}] Transcribed: {user_text}")

    # Step 2: Get Silas Reasoning & Response
    ai_text, thought_tokens, level = await get_gemini_3_response(user_text, device_id, db)
    # Step 3: Return JSON with the TTS URL for ESP32
    encoded_text = urllib.parse.quote(ai_text)
    return {
        "text": ai_text,
        "thought_tokens": thought_tokens,
        "thinking_level": level,
        "audio_url": f"{BASE_URL}/tts?text={encoded_text}" 
    }

@app.post("/chat")
async def handle_chat(
    device_id: str = Form(...),
    user_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handles direct text input for Wokwi simulation."""
    print(f"[{device_id}] Received text (Simulation): {user_text}")
    
    # Reset dashboard UI
    await sio.emit('reset', {})
    
    # Get Silas Reasoning & Response
    ai_text, thought_tokens, level = await get_gemini_3_response(user_text, device_id, db)
    print(f"[{device_id}] Silas: {ai_text}")
    
    # Play TTS through local speakers
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_path = temp_file.name
        
        # Strip markdown before speaking
        speech_text = strip_markdown(ai_text)
        
        # Synthesis for local playback
        input_text = texttospeech.SynthesisInput(text=speech_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-GB", name=SILAS_VOICE)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        
        tts_response = tts_client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
        
        with open(temp_path, "wb") as out:
            out.write(tts_response.audio_content)
        
        # Play audio in background using Windows media player
        def play_audio():
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{temp_path}').PlaySync()"], 
                          capture_output=True, shell=True)
        
        # Use threading to not block the response
        threading.Thread(target=lambda: subprocess.Popen(
            ["powershell", "-c", f"Add-Type -AssemblyName presentationCore; $player = New-Object system.windows.media.mediaplayer; $player.Open('{temp_path}'); $player.Play(); Start-Sleep -Seconds 120"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )).start()
        
        print(f"[TTS] Playing audio through speakers...")
    except Exception as e:
        print(f"[TTS] Playback error: {e}")

    encoded_text = urllib.parse.quote(ai_text)
    return {
        "text": ai_text,
        "thought_tokens": thought_tokens,
        "thinking_level": level,
        "audio_url": f"{BASE_URL}/tts?text={encoded_text}" 
    }

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)