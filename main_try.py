# main.py
# Wake -> Record -> STT -> AI(with memory context) -> TTS -> Silent playback -> Log & persist
# Uses pygame mixer for silent playback WITHOUT opening a player window and keeps looping.

import os
import time
import threading
import pygame  # for silent, in-process audio playback
from wake_engine import wait_for_wake   # your simple wake (press Enter) or replace with porcupine later
from speech_engine import record_audio, stt_google, tts_google
from ai_engine import get_ai_response
from memory_engine_try import MemoryEngine

# -------- Folder setup --------
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR  = os.path.join(BASE_DIR, "logs")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# -------- Init memory --------
memory = MemoryEngine()
profile = memory.load_profile()

# -------- Logging --------
def log_interaction(user_text: str, ai_text: str) -> None:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(LOGS_DIR, "jarvis_logs.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] You: {user_text}\n")
        f.write(f"[{timestamp}] Jarvis: {ai_text}\n\n")

# -------- Auto fact extraction (lightweight & safe) --------
KEYWORDS = (" is ", " are ", " was ", " am ", " like ", " love ", " enjoy ")
def auto_extract_fact(user_text: str):
    """Extremely simple heuristic; avoids nesting and nonsense keys."""
    t = " " + user_text.strip().lower() + " "
    for kw in KEYWORDS:
        if kw in t:
            left, right = t.split(kw, 1)
            # Clean keys like "my name", "favorite color", etc.
            key = left.replace(" my ", " ").strip().strip(" :,-")
            val = right.strip().strip(" .,:;!-")
            if key and val and len(key) <= 50 and len(val) <= 200:
                return key, val
    return None, None

# -------- Silent playback (non-blocking) --------
# Initialize mixer once, up-front (prevents re-init issues across loops)
pygame.mixer.init()

def play_audio_silent(file_path: str):
    """Play MP3 in-process without opening a player window. Non-blocking."""
    def _play(path: str):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            # Wait for playback to finish but do it in this thread so main loop continues
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(30)
        except Exception as e:
            print("⚠️ Audio playback error:", e)

    th = threading.Thread(target=_play, args=(file_path,), daemon=True)
    th.start()

# -------- Main loop --------
def main():
    print(f"🤖 Jarvis online — hello {profile.get('name','User')}!")
    print("Press Enter to wake me. Say 'exit/quit/shutdown' to stop.\n")

    while True:
        # 1) Wake
        wait_for_wake()

        # 2) Record
        ts = time.strftime("%Y%m%d-%H%M%S")
        wav_path = os.path.join(AUDIO_DIR, f"command_{ts}.wav")
        record_audio(filename=wav_path)

        # 3) STT
        user_text = (stt_google(wav_path) or "").strip()
        print(f"📝 You said: {user_text}")

        if not user_text:
            print("…didn't catch that. Try again!")
            continue

        if user_text.lower() in ("exit", "quit", "shutdown"):
            print("👋 Shutting down Jarvis…")
            break

        # 4) Auto-facts: safe, non-nesting facts -> memory
        k, v = auto_extract_fact(user_text)
        if k and v:
            memory.save_memory_fact(k, v)

        # 5) Build memory context for the AI
        context = memory.build_context(user_text, max_history=10)

        # 6) AI
        ai_text = (get_ai_response(context) or "").strip()
        print(f"🤖 Jarvis: {ai_text if ai_text else '[no response]'}")

        # 7) TTS -> MP3
        mp3_path = os.path.join(AUDIO_DIR, f"response_{ts}.mp3")
        try:
            tts_google(ai_text if ai_text else "Sorry, I couldn't process that.", filename=mp3_path)
        except Exception as e:
            print("⚠️ TTS error:", e)
            continue  # skip playback/log if we couldn't synthesize

        # 8) Silent playback (non-blocking; loop continues)
        play_audio_silent(mp3_path)

        # 9) Persist conversation + log
        memory.append_conversation(user_text, ai_text)
        log_interaction(user_text, ai_text)

if __name__ == "__main__":
    main()
