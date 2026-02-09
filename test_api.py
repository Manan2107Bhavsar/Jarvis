import google.generativeai as genai
import config
import os

# Configure API
genai.configure(api_key=config.GEMINI_API_KEY)

def test_model(model_name):
    print(f"Testing model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, are you working?")
        print(f"Success! Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error with {model_name}: {e}")
        return False

# List available models
print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Test available models
test_model('gemini-2.0-flash')
test_model('gemini-2.0-flash-lite')
