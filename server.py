import os
import io
import json
import re
import edge_tts
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
import database
from backend import logic

# Load Environment Variables
load_dotenv(".env.local")
load_dotenv(".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_3_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SILAS_VOICE = "en-GB-RyanNeural" 

client = genai.Client(api_key=GEMINI_API_KEY)

# Load Silas System Prompt
with open("system_prompt.md", "r") as f:
    SILAS_PROMPT = f.read()

app = FastAPI(title="Project Silas: Thinking Hardware Agent")

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

# Mount Dashboard
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

# Database Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return FileResponse("dashboard/index.html")

@app.get("/tts")
async def tts_stream(text: str):
    """Generates Silas's voice and streams it to the ESP32."""
    async def generate():
        communicate = edge_tts.Communicate(text, SILAS_VOICE)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
    return StreamingResponse(generate(), media_type="audio/mpeg")

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

    # Generate Content with Thinking Enabled
    response = client.models.generate_content(
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
    full_response_text = response.text
    new_signature = response.candidates[0].content.parts[-1].thought_signature
    thought_summary = response.thought_summary if hasattr(response, 'thought_summary') else "Analysing circuit..."

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

    # --- Dashboard Update ---
    await sio.emit('new_thought', {'text': thought_summary})
    await sio.emit('thoughts', {
        'device_id': device_id,
        'level': level,
        'summary': thought_summary,
        'text': clean_text,
        'hardware_state': hardware_state
    })

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

    return clean_text

@app.post("/voice")
async def handle_voice(
    device_id: str = Form(...), 
    audio: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Reset dashboard UI
    await sio.emit('reset', {})
    
    audio_bytes = await audio.read()
    
    # Step 1: Transcribe Audio using multimodal capabilities
    transcribe_response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=[
            types.Content(role="user", parts=[
                types.Part(inline_data=types.Blob(mime_type="audio/wav", data=audio_bytes)),
                types.Part(text="Transcribe this audio exactly. Just the text.")
            ])
        ]
    )
    user_text = transcribe_response.text.strip()
    print(f"[{device_id}] Transcribed: {user_text}")

    # Step 2: Get Silas Reasoning & Response
    ai_text = await get_gemini_3_response(user_text, device_id, db)
    print(f"[{device_id}] Silas: {ai_text}")

    # Step 3: Return JSON with the TTS URL for ESP32
    return {
        "text": ai_text,
        "audio_url": f"{BASE_URL}/tts?text={ai_text.replace(' ', '%20')}" 
    }

if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)