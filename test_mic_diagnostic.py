import speech_recognition as sr
import time

def test_mic():
    recognizer = sr.Recognizer()
    print("Available Microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"Index {index}: {name}")
    
    print("\n--- Starting Microphone Test ---")
    try:
        with sr.Microphone() as source:
            print("1. Adjusting for ambient noise (please stay quiet for 1 second)...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold set to: {recognizer.energy_threshold}")
            
            print("\n2. Say 'Hello Jarvis' now...")
            audio = recognizer.listen(source, timeout=10)
            print("3. Audio captured. Processing with Google STT...")
            
            text = recognizer.recognize_google(audio)
            print(f"\n✅ Result: I heard you say: '{text}'")
            
            if "jarvis" in text.lower():
                print("✨ SUCCESS: Wake word 'Jarvis' was correctly identified!")
            else:
                print("⚠️ PARTIAL SUCCESS: Speech was detected, but 'Jarvis' was not in the text.")
                
    except sr.WaitTimeoutError:
        print("❌ ERROR: No speech detected within 10 seconds.")
    except sr.UnknownValueError:
        print("❌ ERROR: Speech was detected but could not be understood.")
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_mic()
