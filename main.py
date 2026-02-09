# main.py

import os
import time
from wake_engine import listen_for_wake_word
from speech_engine import listen_for_command, tts_speak, play_audio_blocking
from ai_engine import get_ai_response
from actions_engine import execute_action
import re

# ---- Folder setup ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

for folder in [LOGS_DIR, AUDIO_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 Created folder: {folder}")

# ---- Logging function ----
def log_interaction(user_text, ai_text):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(LOGS_DIR, "jarvis_logs.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] You: {user_text}\n")
        f.write(f"[{timestamp}] Jarvis: {ai_text}\n\n")

# ---- Main loop ----
def main():
    print("🤖 Jarvis is online!")
    
    while True:
        if listen_for_wake_word():
        
            print("🟢 Entering conversation mode...")
            session_start_time = time.strftime("%Y%m%d-%H%M%S")
            session_history = []  # Initialize session context
            
            while True:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                # Listen for command (Dynamic VAD)
                user_text = listen_for_command()
                
                if user_text:
                    print(f"📝 You said: {user_text}")
                
                if not user_text:
                    print("❓ Didn't catch that. Still listening... (say 'stop' to exit)")
                    continue  # Keep listening instead of breaking
                
                # Check for exit commands
                if user_text.lower() in ["exit", "quit", "shutdown", "stop", "bye"]:
                    print("👋 Exiting conversation mode...")
                    # Save session to file before exiting
                    from memory_engine import save_session_history
                    save_session_history(session_history, session_start_time)
                    break
                
                # Get AI response with session context
                ai_text = get_ai_response(user_text, session_history)
                
                # Check for action triggers
                if "[[" in ai_text and "]]" in ai_text:
                    action_result = execute_action(ai_text)
                    print(f"⚙️ Action: {action_result}")
                    # Clean up the spoken text by removing the action tag
                    ai_text = re.sub(r'\[\[ACTION:.*?\]\]', '', ai_text).strip()

                print(f"🤖 Jarvis: {ai_text}")
                
                # Update session history
                session_history.append(("User", user_text))
                session_history.append(("Jarvis", ai_text))
                
                # Convert AI response to speech
                response_audio = os.path.join(AUDIO_DIR, f"response_{timestamp}.mp3")
                tts_speak(ai_text, filename=response_audio)
                 
                 # Play it automatically (Blocking to prevent self-listening)
                play_audio_blocking(response_audio)
                
                # Log interaction
                log_interaction(user_text, ai_text)


if __name__ == "__main__":
    main()
