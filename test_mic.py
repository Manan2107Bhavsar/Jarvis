import speech_recognition as sr
import time

def test_mic():
    print("🎤 Testing Microphone...")
    r = sr.Recognizer()
    
    # List microphones
    print("\nAvailable Microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{index}: {name}")
        
    print("\n--------------------------------")
    
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... (Please wait)")
        r.adjust_for_ambient_noise(source, duration=1)
        print("✅ Ready. Please say 'Jarvis' or any sentence.")
        
        try:
            print("👂 Listening (5 seconds timeout)...")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("⏳ Processing...")
            
            try:
                text = r.recognize_google(audio)
                print(f"✅ Recognized: '{text}'")
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
            except sr.RequestError as e:
                print(f"❌ Google Speech API error: {e}")
                
        except sr.WaitTimeoutError:
            print("❌ Timeout: No speech detected")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_mic()
