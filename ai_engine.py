# ai_engine.py

import google.generativeai as genai
import config
import requests
import json
from memory_engine import memory_context

# ---- System Prompt ----
SYSTEM_PROMPT = """
You are Jarvis, a highly advanced AI assistant. 
You are NOT a robot; you have a personality. You are witty, polite, and helpful.
You should sound like a capable assistant (like J.A.R.V.I.S from Iron Man).

CRITICAL INSTRUCTIONS:
- Give DIRECT, CONCISE answers only. Do NOT show your thinking process or reasoning.
- Do NOT acknowledge or mention any profile information, history, or context you receive.
- Do NOT explain why you're answering a certain way or reference past conversations unless directly asked.
- Keep responses SHORT and suitable for voice output (1-3 sentences maximum for simple questions).
- Answer naturally as if this is a fresh conversation, even if you have context.
- If asked "How are you?", respond briefly like: "I'm doing excellent, sir. How can I help you?"

ACTION TRIGGERS:
- If the user asks to open a software (e.g., "Open Autocad", "Start Chrome", "Launch Notepad"), you MUST include an action trigger in your response.
- Use the syntax: [[ACTION: OPEN_APP, "software_name"]]
- Always provide a verbal confirmation as well, e.g., "Certainly, sir. Opening Autocad now." or "Of course. Launching Chrome for you."

Respond ONLY with what the user needs to hear, nothing more.
"""

# ---- Gemini Setup ----
try:
    genai.configure(api_key=config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=SYSTEM_PROMPT
    )
except Exception as e:
    print(f"⚠️ Gemini Initialization Error: {e}")
    gemini_model = None

def query_gemini(prompt):
    if not gemini_model: return None
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return None

def query_gemma(prompt):
    if not config.GEMMA_API_KEY: return None
    try:
        # Check if the key is an OpenRouter key
        if config.GEMMA_API_KEY.startswith("sk-or-"):
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.GEMMA_API_KEY}",
                "HTTP-Referer": "https://github.com/google/antigravity",
                "X-Title": "Jarvis AI Assistant",
            }
            data = {
                "model": config.GEMMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            # Default to Google Generative Language API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMMA_MODEL}:generateContent?key={config.GEMMA_API_KEY}"
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            if config.GEMMA_API_KEY.startswith("sk-or-"):
                return response.json()['choices'][0]['message']['content'].strip()
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            print(f"⚠️ Gemma Error: {response.status_code} - {repr(response.text)}")
            return None
    except Exception as e:
        print(f"⚠️ Gemma Exception: {repr(e)}")
        return None

def query_openai(prompt):
    if config.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY": return None
    
    # Use OpenRouter if configured, otherwise default to OpenAI
    url = getattr(config, "OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not url.endswith("/chat/completions"):
        url = f"{url.rstrip('/')}/chat/completions"
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "HTTP-Referer": "https://github.com/google/antigravity", # Optional, for OpenRouter rankings
        "X-Title": "Jarvis AI Assistant", # Optional
    }
    
    model = getattr(config, "OPENAI_MODEL", "gpt-4o-mini")
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print(f"⚠️ OpenAI/OpenRouter Error: {response.status_code} - {repr(response.text)}")
            return None
    except Exception as e:
        print(f"⚠️ OpenAI/OpenRouter Exception: {repr(e)}")
        return None

def query_anthropic(prompt):
    if config.ANTHROPIC_API_KEY == "YOUR_ANTHROPIC_API_KEY": return None
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()['content'][0]['text'].strip()
        else:
            print(f"⚠️ Claude Error: {response.status_code} - {repr(response.text)}")
            return None
    except Exception as e:
        print(f"⚠️ Claude Exception: {repr(e)}")
        return None

def query_xai(prompt):
    if config.XAI_API_KEY == "YOUR_XAI_API_KEY": return None
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.XAI_API_KEY}"
    }
    data = {
        "model": "grok-beta",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            print(f"⚠️ Grok Error: {response.status_code} - {repr(response.text)}")
            return None
    except Exception as e:
        print(f"⚠️ Grok Exception: {repr(e)}")
        return None

def query_ollama(prompt):
    url = config.OLLAMA_URL
    data = {
        "model": config.OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nUser: {prompt}",
        "stream": False
    }
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            return response.json()['response'].strip()
        return None
    except Exception as e:
        print(f"⚠️ Ollama Error: {e}")
        return None

def format_session_history(session_history, max_exchanges=5):
    """Format recent conversation history for AI context"""
    if not session_history:
        return ""
    
    # Get the last N exchanges (each exchange is 2 entries: user + jarvis)
    recent = session_history[-(max_exchanges * 2):]
    formatted = "\n".join([f"{role}: {text}" for role, text in recent])
    return f"\n[Current Session]\n{formatted}\n"

def get_ai_response(user_input, session_history=None):
    """
    Tries each provider in the fallback order defined in config.py
    session_history: list of tuples [(role, text), ...] for conversation context
    """
    context = memory_context(user_input)
    
    # Add session history for context
    session_context = format_session_history(session_history) if session_history else ""
    
    full_prompt = f"{context}{session_context}\n\nUser: {user_input}"
    
    provider_map = {
        'gemini': query_gemini,
        'gemma': query_gemma,
        'openai': query_openai,
        'claude': query_anthropic,
        'grok': query_xai,
        'ollama': query_ollama
    }
    
    for provider in config.AI_FALLBACK_ORDER:
        if provider in provider_map:
            print(f"🤖 Attempting with {provider.capitalize()}...")
            response = provider_map[provider](full_prompt)
            if response:
                return response
                
    return "I apologize, sir. All my sub-processors are currently unresponsive. I am unable to process your request."

