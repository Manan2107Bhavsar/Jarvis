# speech_engine.py
import os
import platform
import pyaudio
import wave
import speech_recognition as sr
import pygame
try:
    from elevenlabs.client import ElevenLabs
except ImportError:
    ElevenLabs = None
    print("⚠️ ElevenLabs module not available (ImportError).")
from google.cloud import speech, texttospeech
from google.oauth2 import service_account
import config
import requests

# Initialize Google Cloud credentials
credentials = service_account.Credentials.from_service_account_file(config.GOOGLE_KEY_PATH)
speech_client = speech.SpeechClient(credentials=credentials)
tts_client = texttospeech.TextToSpeechClient(credentials=credentials)

def record_audio(filename="command.wav", duration=10):
    """
    Record audio from microphone
    """
    chunk = 1024
    format = pyaudio.paInt16
    p = pyaudio.PyAudio()
    
    stream = p.open(format=format, channels=config.CHANNELS, rate=config.SAMPLE_RATE, input=True, frames_per_buffer=chunk)
    
    print("🎤 Recording...")
    frames = [stream.read(chunk) for _ in range(0, int(config.SAMPLE_RATE / chunk * duration))]
    
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(config.CHANNELS)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(config.SAMPLE_RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"✅ Audio saved as {filename}")
    return filename

def tts_google(text, filename="response.mp3"):
    """
    Google Cloud Text-to-Speech
    """
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    with open(filename, "wb") as out:
        out.write(response.audio_content)
    
    print(f"🗣 Response saved as {filename}")
    return filename

def play_audio(file_path):
    """
    Play audio file automatically depending on OS
    """
    if platform.system() == "Windows":
        os.startfile(file_path)  # Uses default media player
    elif platform.system() == "Darwin":  # macOS
        os.system(f"afplay '{file_path}'")
    else:  # Linux
        os.system(f"mpg123 '{file_path}'")  # Make sure mpg123 is installed

# ---- ElevenLabs TTS Provider ----
def query_elevenlabs(text, filename="response.mp3"):
    """
    ElevenLabs TTS using raw HTTP (requests).
    Returns filename if successful, None otherwise.
    """
    if config.ELEVEN_LABS_API_KEY == "YOUR_ELEVEN_LABS_API_KEY": return None
    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech/nPczCjzI2devNBz1zQrb"  # Brian voice
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": config.ELEVEN_LABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        print("🗣 Requesting ElevenLabs Audio...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"🗣 ElevenLabs Response saved as {filename}")
            return filename
        else:
            print(f"⚠️ ElevenLabs API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ ElevenLabs Connection Error: {e}")
        return None

# ---- Google TTS Provider ----
def query_google_tts(text, filename="response.mp3"):
    """
    Google Cloud Text-to-Speech provider.
    """
    try:
        return tts_google(text, filename)
    except Exception as e:
        print(f"⚠️ Google TTS Error: {e}")
        return None

# ---- Unified TTS Dispatcher ----
def tts_speak(text, filename="response.mp3"):
    """
    Main entry point for TTS. Follows config.TTS_FALLBACK_ORDER.
    """
    provider_map = {
        'elevenlabs': query_elevenlabs,
        'google': query_google_tts
    }
    
    for provider in config.TTS_FALLBACK_ORDER:
        if provider in provider_map:
            print(f"🗣 Attempting TTS with {provider.capitalize()}...")
            result = provider_map[provider](text, filename)
            if result:
                return result
                
    print("⚠️ All TTS providers failed.")
    return None

def play_audio_blocking(file_path):
    """
    Play audio and wait until it finishes (Blocking)
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print("⚠️ Could not play audio:", e)

def listen_for_command():
    """
    Listen for a command using SpeechRecognition (VAD)
    Returns text directly. Falls back to Google Cloud STT if standard fails.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            # Listen indefinitely until silence is detected
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=None) 
            print("⏳ Processing...")
            
            try:
                # Primary: Standard Google Speech API (Free)
                text = recognizer.recognize_google(audio)
                return text
            except Exception as e:
                print(f"⚠️ Standard STT failed: {e}. Trying Google Cloud STT...")
                
                # Fallback: Google Cloud Speech-to-Text (Paid/Credentials)
                try:
                    content = audio.get_wav_data()
                    audio_req = speech.RecognitionAudio(content=content)
                    config_req = speech.RecognitionConfig(
                        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=config.SAMPLE_RATE,
                        language_code="en-US",
                    )
                    response = speech_client.recognize(config=config_req, audio=audio_req)
                    
                    if response.results:
                        text = response.results[0].alternatives[0].transcript
                        print(f"✅ Google Cloud STT Success: {text}")
                        return text
                    return None
                except Exception as e2:
                    print(f"⚠️ Google Cloud STT failed: {e2}")
                    return None
                    
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"⚠️ Error listening: {e}")
            return None