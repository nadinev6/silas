"""
Silas Local Client - Talk to Silas with TTS Playback

This script lets you chat with Silas from your terminal and hear his 
response through your speakers using edge-tts and pygame.

Usage:
    python silas_client.py

Requirements:
    pip install edge-tts pygame requests
"""

import asyncio
import tempfile
import os
import requests
import pygame

# Configuration
SERVER_URL = os.getenv("SILAS_URL", "http://localhost:8000")
DEVICE_ID = "local-client-01"
SILAS_VOICE = "en-GB-RyanNeural"  # British voice for Silas

# Initialize pygame mixer for audio playback
pygame.mixer.init()

async def text_to_speech(text: str) -> str:
    """Generate TTS audio using edge-tts and return the temp file path."""
    import edge_tts
    
    # Create a temp file for the audio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_path = temp_file.name
    temp_file.close()
    
    communicate = edge_tts.Communicate(text, SILAS_VOICE)
    await communicate.save(temp_path)
    
    return temp_path

def play_audio(file_path: str):
    """Play an MP3 file using pygame."""
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    
    # Wait for playback to finish
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    # Clean up temp file
    try:
        os.remove(file_path)
    except:
        pass

def ask_silas(user_text: str) -> str:
    """Send a message to Silas and get his response."""
    try:
        response = requests.post(
            f"{SERVER_URL}/chat",
            data={"device_id": DEVICE_ID, "user_text": user_text}
        )
        if response.status_code == 200:
            return response.json().get("text", "")
        else:
            return f"[Error: HTTP {response.status_code}]"
    except Exception as e:
        return f"[Error: {str(e)}]"

async def main():
    print("\n" + "="*50)
    print("  🛠️  SILAS LOCAL CLIENT - Voice Enabled")
    print("="*50)
    print(f"Server: {SERVER_URL}")
    print("Type your question and press Enter.")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("Silas is thinking...")
            
            # Get Silas's response
            response = ask_silas(user_input)
            print(f"\n🛠️ Silas: {response}\n")
            
            # Generate and play TTS
            if response and not response.startswith("[Error"):
                print("(Speaking...)")
                audio_path = await text_to_speech(response)
                play_audio(audio_path)
                print()
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())
