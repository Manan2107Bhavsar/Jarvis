# main.py

import os
import time
from wake_engine import wait_for_wake
from speech_engine import record_audio, stt_google, tts_google, play_audio_silent
from ai_engine import get_ai_response
from memory_engine_try import MemoryEngine

# ---- Folder setup ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
for folder in [LOGS_DIR, AUDIO_DIR]:
    os.makedirs(folder, exist_ok=True)

# ---- Initialize memory engine ----
memory = MemoryEngine()
profile = memory.load_profile()
user_memory = memory.load_memory()
conversation_history = memory.load_conversation()

# ---- Logging function ----
def log_interaction(user_text, ai_text):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(LOGS_DIR, "jarvis_logs.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] You: {user_text}\n")
        f.write(f"[{timestamp}] Jarvis: {ai_text}\n\n")

# ---- Automatic fact extraction ----
def auto_extract_facts(user_input):
    keywords = ["is", "are", "was", "am", "like", "love", "enjoy"]
    for kw in keywords:
        if kw in user_input:
            parts = user_input.split(kw)
            if len(parts) >= 2:
                topic = parts[0].replace("my", "").strip()
                fact = parts[1].strip()
                return topic, fact
    return None, None

def save_fact(topic, fact):
    if topic and fact:
        user_memory[topic] = fact
        memory.save_memory(user_memory)

def save_conversation(user_text, ai_text):
    conversation_history.append({"user": user_text, "ai": ai_text})
    memory.save_conversation(conversation_history)

# ---- Build memory context ----
def build_context(user_input):
    context_parts = []

    # Profile info
    context_parts.append(f"[PROFILE] name={profile.get('name')} timezone={profile.get('timezone')}")

    # Memory facts
    if user_memory:
        facts_text = "; ".join([f"{k}={v}" for k, v in user_memory.items()])
        context_parts.append(f"[FACTS] {facts_text}")

    # Previous conversation
    if conversation_history:
        conv_text = "; ".join([f"You: {c['user']} | Jarvis: {c['ai']}" for c in conversation_history])
        context_parts.append(f"[CONVERSATION HISTORY] {conv_text}")

    # Current user input
    context_parts.append(f"[USER INPUT] {user_input}")

    return "\n".join(context_parts)

# ---- Main loop ----
def main():
    print(f"🤖 Jarvis is online! Hello {profile.get('name')}")

    while True:
        wait_for_wake()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        audio_file = os.path.join(AUDIO_DIR, f"command_{timestamp}.wav")

        # Record user speech
        record_audio(filename=audio_file)
        user_text = stt_google(audio_file)
        print(f"📝 You said: {user_text}")

        if user_text.lower() in ["exit", "quit", "shutdown"]:
            print("👋 Shutting down Jarvis...")
            break

        # Automatic fact extraction
        topic, fact = auto_extract_facts(user_text.lower())
        if topic and fact:
            save_fact(topic, fact)

        # Build context and get AI response
        context = build_context(user_text)
        ai_text = get_ai_response(context)
        print(f"🤖 Jarvis: {ai_text}")

        # TTS and silent playback
        response_audio = os.path.join(AUDIO_DIR, f"response_{timestamp}.mp3")
        tts_google(ai_text, filename=response_audio)
        play_audio_silent(response_audio)

        # Save conversation & log
        save_conversation(user_text, ai_text)
        log_interaction(user_text, ai_text)

if __name__ == "__main__":
    main()
