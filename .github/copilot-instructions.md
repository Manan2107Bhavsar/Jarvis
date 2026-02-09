# Jarvis AI Assistant - Copilot Instructions

## Project Overview

**Jarvis** is a voice-activated AI assistant with a J.A.R.V.I.S (Iron Man) personality. It combines speech recognition, AI generation, and text-to-speech into a conversational system that includes both CLI and web UI interfaces.

### Core Architecture

Jarvis follows a **modular engine-based architecture** with these key components:

1. **Wake Engine** (`wake_engine.py`) - Always-listening wake word detector using Google Speech Recognition
2. **Speech Engine** (`speech_engine.py`) - Dual-mode STT/TTS handling (Google Cloud + ElevenLabs fallback)
3. **AI Engine** (`ai_engine.py`) - Gemini 2.0 Flash integration with stateful chat history
4. **Memory Engine** (`memory_engine.py`) - Persistent context: user profile, memorized facts, search history
5. **WebSocket Server** (`websocket_server.py`) - Real-time bi-directional communication with web UI
6. **Web UI** (`ui/`) - Particle-animated HUD interface with conversation logging

### Data Flow

```
[Microphone] → Wake Engine → Speech Engine (STT) 
                                    ↓
                           [Memory Context] → AI Engine (Gemini)
                                    ↑
                           [Gemini Response] → Speech Engine (TTS)
                                    ↓
                           [Audio Output] → User
                                    ↓
                           [Interaction Log] → memory/history.jsonl + logs/
```

## Critical Developer Knowledge

### 1. Configuration & Secrets Management

- **File**: `config.py` - All API keys and audio settings centralized here
- **Keys**:
  - `GOOGLE_KEY_PATH`: Service account JSON for Cloud STT/TTS
  - `GEMINI_API_KEY`: Direct string key (currently hardcoded - consider env variable)
  - `ELEVEN_LABS_API_KEY`: Backup TTS provider
  - Audio params: `AUDIO_DURATION`, `SAMPLE_RATE`, `CHANNELS` (all used by speech_engine)

**Convention**: Always import config first and reference via `config.CONSTANT_NAME` rather than defining locally.

### 2. Memory & Persistence Pattern

Memory is **context-injected** into every AI request, not part of chat session:

```python
# In memory_engine.py:
def memory_context(user_query: str = "") -> str:
    """Combines profile + facts + relevant history into prompt context"""
    profile = load_profile()  # From profile.json
    facts = load_memory()      # From memory.json (facts key)
    history = search_history(user_query)  # JSONL file search
```

**Key files**:
- `profile.json` - User metadata (name, timezone, location, study program)
- `memory.json` - Simple {"facts": [...]} structure for memorized facts
- `memory/history.jsonl` - One JSON object per line; stores full conversation logs

**Pattern**: Always use `memory_context(user_input)` when calling `get_ai_response()`. This ensures the AI has relevant context without maintaining conversation state server-side.

### 3. Speech Recognition Edge Cases

`speech_engine.py` handles multiple failure modes:

- **No speech detected** → `UnknownValueError` caught, returns `None`
- **Timeout** → `WaitTimeoutError` after 10s listening
- **Network/API failure** → Exception caught, fallback to Gemini lite model

**Important**: `listen_for_command()` uses indefinite listening (`phrase_time_limit=None`), so it waits for natural silence. The wake engine uses shorter timeouts (3-4s) for efficiency.

### 4. TTS Dual Provider Strategy

Default provider: **ElevenLabs** (superior voice quality)
Fallback: **Google Cloud TTS** (if ElevenLabs fails)

```python
# speech_engine.py pattern:
tts_elevenlabs(text, filename)  # Primary
# Internally handles fallback to tts_google() on exception
```

Audio playback uses **pygame.mixer** for blocking playback (critical: prevents wake engine from detecting Jarvis's own voice).

### 5. AI Engine Conversation State

**Gemini maintains stateful chat history** across interactions:

```python
chat = model.start_chat(history=[])  # Created once at module load
# Each call to chat.send_message() appends to this history
```

**Important gotcha**: Chat session can fail if:
- API quota exceeded
- Network timeout
- Token limit in conversation

**Fallback**: Catches exception and retries with `gemini-2.0-flash-lite` (lighter model).

### 6. WebSocket Real-Time Communication

Server broadcasts state updates to all connected clients:

```python
# websocket_server.py pattern:
jarvis_state = {
    'current_state': 'idle',     # idle, listening, processing, speaking
    'is_running': False
}
async def broadcast_message(message: Dict[str, Any]):
    # Sends to all connected_clients
```

Web UI (`ui/app.js`) subscribes and updates:
- Particle animations (listening/processing/speaking states)
- Real-time conversation log display
- Neural status indicators

**Port**: 8765 (hardcoded - consider config.py addition)

## Project-Specific Patterns & Conventions

### Logging

- **Interaction logs**: `logs/jarvis_logs.txt` - Plain text, timestamp + speaker format
- **Conversation history**: `memory/history.jsonl` - Machine-readable, enables search
- **Audio files**: `audio/` directory, timestamped (e.g., `response_20251209-143022.mp3`)

### Emoji Usage in Output

Output heavily uses emoji for visual feedback (not just decoration):
```python
"✨ Wake word detected!"
"🎤 Recording..."
"🤖 Jarvis: [response]"
```
This is intentional for CLI usability on Windows PowerShell (note the reconfigure call in websocket_server.py).

### Exit Conditions

Main conversation loop breaks on:
- No speech detected (silence timeout)
- User says: "exit", "quit", "shutdown", "stop", "bye" (case-insensitive)

### Error Messages

Fallback message is: `"I apologize, sir. I am having trouble connecting to my neural network."`

This matches the J.A.R.V.I.S personality.

## Testing & Debugging

**Test files** (not integrated into main flow):
- `test_api.py` - Gemini API connectivity
- `test_mic.py`, `test_microphone.py` - Microphone I/O
- `test_memory.py` - Memory persistence
- `test_elevenlabs.py` - ElevenLabs TTS

**Try/test versions**:
- `ai_engine_try.py`, `main_try.py`, `memory_engine_try.py` - Experimental code (not imported by main)

**Manual fixes**:
- `MANUAL_FIX_app_js.txt` - Documents known UI issues (check before modifying `ui/app.js`)

## Common Tasks

### Add a New Command Handler
1. Update `main.py` exit condition check to include your command
2. Add response logic before `get_ai_response()` call
3. Log interaction with `log_interaction(user_text, ai_text)`

### Extend Memory System
1. Add key to `profile.json` default in `memory_engine.py:load_profile()`
2. Create update function following `update_profile()` pattern
3. Inject into prompt via `memory_context()` string builder

### Modify AI Personality
1. Edit `SYSTEM_PROMPT` in `ai_engine.py` (currently hardcoded)
2. Test with `test_api.py` before committing
3. Consider that Gemini maintains state across calls - may need to restart for personality shift to take effect

### Add WebSocket Event
1. Create message type in `websocket_server.py` (check existing patterns)
2. Add handler in `async def handle_client()`
3. Update `ui/app.js` to subscribe and respond to message type

## File Organization Reference

```
.github/
  copilot-instructions.md       # This file

Core Engines:
  wake_engine.py                # Wake word detection
  speech_engine.py              # STT + TTS + audio playback
  ai_engine.py                  # Gemini integration + system prompt
  memory_engine.py              # Profile/facts/history persistence
  config.py                      # All secrets and constants

Entry Points:
  main.py                       # CLI version (wake → listen loop)
  websocket_server.py           # Web UI backend

UI:
  ui/app.js                     # Particle HUD + WebSocket client
  ui/index.html                 # Layout
  ui/style.css, styles.css      # Styling

Data:
  profile.json                  # User metadata
  memory.json                   # Memorized facts
  memory/history.jsonl          # Conversation history (JSONL format)
  logs/jarvis_logs.txt          # Plain-text interaction logs
  audio/                        # Generated audio files

Docs:
  docs/folder_structure_ideas.md # Future UI enhancements
```

## Dependencies

**Python**: Requires Google Cloud credentials file, ElevenLabs API key, Gemini API key

**Key packages** (see `requirements.txt`):
- `google-generativeai` - Gemini API
- `google-cloud-speech`, `google-cloud-texttospeech` - Cloud STT/TTS
- `elevenlabs` - Premium voice synthesis
- `SpeechRecognition` - Wake word + local recognition
- `pyaudio` - Microphone access
- `pygame` - Audio playback
- `websockets` - Real-time server communication

**Note**: Ensure Google Cloud service account JSON is placed at path specified in `config.py:GOOGLE_KEY_PATH`.

## Known Limitations & Future Work

- Gemini chat history unbounded (may hit token limits on long sessions)
- WebSocket port hardcoded - should be moved to config.py
- Memory search is linear scan of entire JSONL file (scalability concern for 25MB+ files)
- AI response requires full system prompt injection on every request (not streaming)

Refer to `docs/folder_structure_ideas.md` for UI conversation organization enhancements being considered.
