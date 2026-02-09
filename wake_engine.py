import speech_recognition as sr
import config

def listen_for_wake_word():
    """
    Listens for the wake word "Jarvis" using SpeechRecognition.
    Returns True if detected.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        # Only adjust for noise occasionally or with shorter duration
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        
        try:
            print("👂 Listening for 'Jarvis'...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            print("⏳ Processing wake word...")
            text = recognizer.recognize_google(audio).lower()
            print(f"🎤 Heard: '{text}'")
            
            if "jarvis" in text:
                print("✨ Wake word detected!")
                return True
        except sr.WaitTimeoutError:
            return False
        except sr.UnknownValueError:
            # This means it heard something but couldn't understand it
            # print("❓ Could not understand audio")
            return False
        except Exception as e:
            print(f"⚠️ Wake word error: {e}")
            return False
            
    return False
