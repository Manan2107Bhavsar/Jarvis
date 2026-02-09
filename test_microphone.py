"""
Simple microphone test script to verify speech recognition is working
"""
import speech_recognition as sr

def test_microphone():
    recognizer = sr.Recognizer()
    
    print("🎤 Testing microphone...")
    print("Available microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  [{index}] {name}")
    
    print("\n🎤 Speak something (you have 5 seconds)...")
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("✅ Ready! Speak now...")
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("⏳ Processing audio...")
            
            text = recognizer.recognize_google(audio)
            print(f"✅ You said: '{text}'")
            
            if "jarvis" in text.lower():
                print("🎉 Wake word 'Jarvis' detected!")
            else:
                print(f"ℹ️ Wake word not in speech. Try saying 'Hey Jarvis' or 'Jarvis'")
                
        except sr.WaitTimeoutError:
            print("⚠️ Timeout - No speech detected within 5 seconds")
        except sr.UnknownValueError:
            print("⚠️ Could not understand audio")
        except sr.RequestError as e:
            print(f"❌ Google API error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_microphone()
