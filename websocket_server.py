# websocket_server.py
"""
WebSocket server for J.A.R.V.I.S UI
Provides real-time communication between the web interface and Jarvis backend
"""

import asyncio
import websockets
import json
import time
import threading
import sys
import os
import queue

# Global command queue for text input
command_queue = queue.Queue()

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from datetime import datetime
from typing import Set, Dict, Any

# Import existing Jarvis modules
from wake_engine import listen_for_wake_word
from speech_engine import listen_for_command, tts_speak, play_audio_blocking
from ai_engine import get_ai_response
from actions_engine import execute_action
import os
import re

# Configuration
HOST = 'localhost'
PORT = 8765
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Connected clients
connected_clients: Set[websockets.WebSocketServerProtocol] = set()

# Global state
jarvis_state = {
    'current_state': 'idle',  # idle, listening, processing, speaking
    'is_running': False
}


async def broadcast_message(message: Dict[str, Any]):
    """Broadcast a message to all connected clients"""
    if connected_clients:
        message_json = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_json) for client in connected_clients],
            return_exceptions=True
        )


async def send_status_update(status: Dict[str, str]):
    """Send system status update to all clients"""
    await broadcast_message({
        'type': 'status',
        'payload': status
    })


async def send_state_change(state: str):
    """Send state change notification to all clients"""
    jarvis_state['current_state'] = state
    await broadcast_message({
        'type': 'state_change',
        'payload': {'state': state}
    })


async def send_user_speech(text: str):
    """Send user speech to all clients"""
    await broadcast_message({
        'type': 'user_speech',
        'payload': {
            'text': text,
            'timestamp': datetime.now().isoformat()
        }
    })


async def send_jarvis_response(text: str, response_time: int = None):
    """Send Jarvis response to all clients"""
    await broadcast_message({
        'type': 'jarvis_response',
        'payload': {
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'responseTime': response_time
        }
    })


async def send_error(message: str):
    """Send error message to all clients"""
    await broadcast_message({
        'type': 'error',
        'payload': {'message': message}
    })


async def handle_get_history(websocket):
    """Handle request for conversation history"""
    try:
        history_file = os.path.join(BASE_DIR, "memory", "history.jsonl")
        
        if not os.path.exists(history_file):
            await websocket.send(json.dumps({
                'type': 'history_data',
                'payload': {'history': [], 'error': 'No history file found'}
            }))
            return
        
        history_items = []
        with open(history_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        history_items.append(item)
                    except json.JSONDecodeError:
                        continue
        
        # Send history data to client
        await websocket.send(json.dumps({
            'type': 'history_data',
            'payload': {'history': history_items}
        }))
        
        print(f"📚 Sent {len(history_items)} history items to client")
        
    except Exception as e:
        print(f"❌ Error loading history: {e}")
        await websocket.send(json.dumps({
            'type': 'history_data',
            'payload': {'history': [], 'error': str(e)}
        }))


def save_to_history(role: str, text: str, timestamp: str):
    """Save conversation item to history file"""
    try:
        history_file = os.path.join(BASE_DIR, "memory", "history.jsonl")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        entry = {
            "role": role,
            "text": text,
            "timestamp": timestamp
        }
        
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            
    except Exception as e:
        print(f"❌ Error saving history: {e}")


# Global event loop reference
MAIN_LOOP = None

def run_async(coro):
    """Run an async coroutine from a different thread safely"""
    if MAIN_LOOP and MAIN_LOOP.is_running():
        try:
            future = asyncio.run_coroutine_threadsafe(coro, MAIN_LOOP)
            return future.result()
        except Exception as e:
            print(f"❌ Error running async: {e}")
            coro.close()
            return None
    else:
        # Loop not ready yet, just clean up
        coro.close()
        return None

# Event for wake word detection
wake_word_event = threading.Event()

# Queue for passing wake word text to jarvis_loop
wake_word_result_queue = queue.Queue()

def wake_word_listener():
    """Run wake word detection in a separate thread"""
    print("👂 Wake word listener thread started")
    while jarvis_state['is_running']:
        try:
            # Only listen if we are in idle state (allow headless)
            if jarvis_state['current_state'] == 'idle':
                # listen_for_wake_word now returns either False or the transcript string
                wake_text = listen_for_wake_word()
                if wake_text:
                    print(f"🟢 Wake word detected (Thread): '{wake_text}'")
                    wake_word_result_queue.put(wake_text)
                    wake_word_event.set()
                    # Wait for state to change before checking again
                    while jarvis_state['current_state'] == 'idle' and jarvis_state['is_running'] and wake_word_event.is_set():
                        time.sleep(0.1)
            else:
                time.sleep(0.5)
        except Exception as e:
            print(f"❌ Error in wake word listener: {e}")
            time.sleep(1)

def jarvis_loop():
    """Main Jarvis loop running in a separate thread"""
    print("🤖 Jarvis is online!")
    
    # Start wake word listener thread
    wake_thread = threading.Thread(target=wake_word_listener, daemon=True)
    wake_thread.start()
    
    while jarvis_state['is_running']:
        try:
            # Check for text command first (Non-blocking)
            try:
                user_text = command_queue.get_nowait()
                print(f"📨 Processing text command: {user_text}")
                wake_word_detected = True
            except queue.Empty:
                user_text = None
                wake_word_detected = False

            # Check for wake word event (Non-blocking)
            if not wake_word_detected and wake_word_event.is_set():
                print("🟢 Wake word event received!")
                wake_word_event.clear()
                wake_word_detected = True
                
                # Check if there's trailing text after "Jarvis"
                try:
                    full_wake_text = wake_word_result_queue.get_nowait()
                    # Try to find "jarvis" and take everything after it
                    match = re.search(r'jarvis\s*(.*)', full_wake_text.lower())
                    if match:
                        potential_command = match.group(1).strip()
                        if potential_command:
                            print(f"💬 Extracted command from wake word: '{potential_command}'")
                            user_text = potential_command
                except queue.Empty:
                    pass
            
            # If nothing detected, loop again (short sleep to prevent CPU hogging)
            if not wake_word_detected:
                run_async(send_state_change('idle'))
                run_async(send_status_update({
                    'voiceRecognition': 'Standby',
                    'processing': 'Idle'
                }))
                time.sleep(0.1)
                continue
            
            # === CONVERSATION MODE ===
            if wake_word_detected:
                print("🟢 Entering conversation mode...")
                session_start_time = time.strftime("%Y%m%d-%H%M%S")
                session_history = []  # Initialize session context
                
                # Continuous conversation loop
                while jarvis_state['is_running']:
                    # Enter conversation mode
                    run_async(send_state_change('listening'))
                    run_async(send_status_update({
                        'voiceRecognition': 'Active'
                    }))
                    
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    
                    # If we already have text (from queue), use it. Otherwise listen.
                    if not user_text:
                        # Check for new text commands from queue (non-blocking)
                        try:
                            user_text = command_queue.get_nowait()
                            print(f"📨 Processing text command: {user_text}")
                        except queue.Empty:
                            # Listen for voice command
                            jarvis_state['current_state'] = 'listening'
                            user_text = listen_for_command()
                    
                    if not user_text:
                        print("❓ Didn't catch that. Still listening... (say 'stop' to exit)")
                        user_text = None  # Reset for next iteration
                        continue  # Keep listening instead of breaking
                    
                    print(f"📝 You said: {user_text}")
                    run_async(send_user_speech(user_text))
                    save_to_history("user", user_text, timestamp)
                    
                    # Check for exit commands
                    if user_text.lower() in ["exit", "quit", "shutdown", "stop", "bye"]:
                        print("👋 Exiting conversation mode...")
                        # Save session to file before exiting
                        from memory_engine import save_session_history
                        save_session_history(session_history, session_start_time)
                        jarvis_state['current_state'] = 'idle'
                        user_text = None  # Reset
                        break  # Exit conversation loop
                    
                    # Process with AI (with session context)
                    run_async(send_state_change('processing'))
                    run_async(send_status_update({
                        'processing': 'Active'
                    }))
                    
                    start_time = time.time()
                    ai_text = get_ai_response(user_text, session_history)
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # Check for action triggers
                    if "[[" in ai_text and "]]" in ai_text:
                        actions = re.findall(r'\[\[ACTION:.*?\]\]', ai_text)
                        for action in actions:
                            action_result = execute_action(action)
                            print(f"⚙️ Action: {action_result}")
                        # Clean up the text by removing all action tags for UI and TTS
                        ai_text = re.sub(r'\[\[ACTION:.*?\]\]', '', ai_text).strip()

                    print(f"🤖 Jarvis: {ai_text}")
                    run_async(send_jarvis_response(ai_text, response_time))
                    save_to_history("jarvis", ai_text, timestamp)
                    
                    # Update session history
                    session_history.append(("User", user_text))
                    session_history.append(("Jarvis", ai_text))
                    
                    # Generate and play speech
                    run_async(send_state_change('speaking'))
                    run_async(send_status_update({
                        'audioOutput': 'Playing'
                    }))
                    
                    response_audio = os.path.join(AUDIO_DIR, f"response_{timestamp}.mp3")
                    tts_speak(ai_text, filename=response_audio)
                    play_audio_blocking(response_audio)
                    
                    # Log interaction
                    log_file = os.path.join(LOGS_DIR, "jarvis_logs.txt")
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] You: {user_text}\n")
                        f.write(f"[{timestamp}] Jarvis: {ai_text}\n\n")
                    
                    # Reset user_text for next iteration
                    user_text = None
                    # DO NOT reset state to idle - keep in conversation mode!
                    
        except Exception as e:
            print(f"❌ Error in Jarvis loop: {e}")
            run_async(send_error(str(e)))
            jarvis_state['current_state'] = 'idle'
            time.sleep(1)



async def handle_client_message(websocket, message: str):
    """Handle incoming messages from clients"""
    try:
        data = json.loads(message)
        message_type = data.get('type')
        
        if message_type == 'manual_trigger':
            # Manual voice command trigger from UI
            print("🎤 Manual voice command triggered from UI")
            # You could implement manual trigger logic here
            
        elif message_type == 'text_command':
            # Text command from UI
            text = data.get('payload', {}).get('text')
            if text:
                print(f"📩 Received text command: {text}")
                command_queue.put(text)
            
        elif message_type == 'get_status':
            # Send current status
            await send_status_update({
                'voiceRecognition': 'Standby' if jarvis_state['current_state'] == 'idle' else 'Active',
                'audioOutput': 'Playing' if jarvis_state['current_state'] == 'speaking' else 'Ready',
                'processing': 'Active' if jarvis_state['current_state'] == 'processing' else 'Idle'
            })
            
        elif message_type == 'get_history':
            # Send conversation history
            await handle_get_history(websocket)
            
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON received: {message}")
    except Exception as e:
        print(f"❌ Error handling message: {e}")


async def websocket_handler(websocket, path=None):
    """Handle WebSocket connections"""
    # Register client
    connected_clients.add(websocket)
    client_id = id(websocket)
    print(f"✅ Client connected: {client_id}")
    
    try:
        # Send initial status
        await websocket.send(json.dumps({
            'type': 'status',
            'payload': {
                'voiceRecognition': 'Standby',
                'audioOutput': 'Ready',
                'processing': 'Idle'
            }
        }))
        
        await websocket.send(json.dumps({
            'type': 'state_change',
            'payload': {'state': jarvis_state['current_state']}
        }))
        
        # Listen for messages
        async for message in websocket:
            await handle_client_message(websocket, message)
            
    except websockets.exceptions.ConnectionClosed:
        print(f"❌ Client disconnected: {client_id}")
    finally:
        connected_clients.discard(websocket)


async def start_server():
    """Start the WebSocket server"""
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    print(f"🚀 Starting WebSocket server on ws://{HOST}:{PORT}")
    
    async with websockets.serve(websocket_handler, HOST, PORT):
        print(f"✅ WebSocket server running on ws://{HOST}:{PORT}")
        print(f"🌐 Open ui/index.html in your browser to access the UI")
        
        # Start Jarvis loop in a separate thread AFTER loop is ready
        if not jarvis_state['is_running']:
            jarvis_state['is_running'] = True
            jarvis_thread = threading.Thread(target=jarvis_loop, daemon=True)
            jarvis_thread.start()
            print("🤖 Jarvis logic thread started")

        await asyncio.Future()  # Run forever


def main():
    """Main entry point"""
    # Create necessary directories
    for folder in [LOGS_DIR, AUDIO_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Created folder: {folder}")
    
    # Start WebSocket server
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        jarvis_state['is_running'] = False


if __name__ == "__main__":
    main()
