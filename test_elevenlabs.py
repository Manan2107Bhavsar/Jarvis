from elevenlabs.client import ElevenLabs
import config

# Test ElevenLabs API
client = ElevenLabs(api_key=config.ELEVEN_LABS_API_KEY)

# Check what methods are available
print("Client type:", type(client))
print("Client attributes:", dir(client))

# Try to generate audio
try:
    print("\nTrying generate method...")
    audio = client.generate(text="Test", voice="Brian")
    print("generate() works!")
except AttributeError as e:
    print(f"generate() failed: {e}")
    
try:
    print("\nTrying text_to_speech.convert method...")
    audio = client.text_to_speech.convert(text="Test", voice_id="nPczCjzI2devNBz1zQrb")
    print("text_to_speech.convert() works!")
except AttributeError as e:
    print(f"text_to_speech.convert() failed: {e}")
