# test_fallbacks.py
import config
import ai_engine
import requests
import json

def test_provider(name, func):
    print(f"\n--- Testing Provider: {name} ---")
    try:
        response = func("Identify yourself and check connection.")
        if response:
            print(f"✅ {name} Success: {response}")
        else:
            print(f"❌ {name} failed (check console for status code)")
    except Exception as e:
        print(f"❌ {name} error: {e}")

if __name__ == "__main__":
    providers = {
        'Gemini': ai_engine.query_gemini,
        'Gemma': ai_engine.query_gemma,
        'Grok': ai_engine.query_xai,
        'Claude': ai_engine.query_anthropic,
        'OpenAI': ai_engine.query_openai,
        'Ollama': ai_engine.query_ollama
    }
    
    for name, func in providers.items():
        test_provider(name, func)
