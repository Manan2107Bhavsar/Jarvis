import json, os
import glob

# Ensure dirs exist
os.makedirs("log", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("memory", exist_ok=True)

PROFILE_FILE = "profile.json"
MEMORY_FILE = "memory.json"
HISTORY_FILE = os.path.join("memory", "history.jsonl")

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        default = {"name": "Manan", "timezone": "America/Regina", "study": "", "location": ""}
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def update_profile(key: str, value: str):
    data = load_profile()
    data[key] = value
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return f"Updated {key} to {value}"

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"facts": []}, f, indent=2)
        return {"facts": []}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(fact: str):
    data = load_memory()
    data["facts"].append(fact)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def search_history(query: str, limit=5):
    """Search imported history for keywords"""
    results = []
    if not os.path.exists(HISTORY_FILE):
        return results
        
    query = query.lower()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # Read file in reverse or just scan all? 25MB is scanable.
            # Let's just scan all for now, maybe optimize later.
            for line in f:
                if query in line.lower():
                    try:
                        entry = json.loads(line)
                        results.append(f"[{entry['timestamp']}] {entry['role']}: {entry['text']}")
                        if len(results) >= limit:
                            break
                    except:
                        continue
    except Exception as e:
        print(f"Error searching history: {e}")
        
    return results

def memory_context(user_query: str = "") -> str:
    """Combine profile + remembered facts + relevant history into one context string"""
    profile = load_profile()
    mem = load_memory()

    context = []
    
    # Profile Section - Make it subtle, not explicit
    profile_parts = []
    if profile.get('name'):
        profile_parts.append(f"User's name: {profile.get('name')}")
    if profile.get('location'):
        profile_parts.append(f"Location: {profile.get('location')}")
    if profile.get('study'):
        profile_parts.append(f"Studies: {profile.get('study')}")
    
    if profile_parts:
        context.append("Context: " + ", ".join(profile_parts) + ".")

    # Facts Section - Only if there are facts
    if mem.get("facts") and len(mem["facts"]) > 0:
        context.append("Known facts: " + "; ".join(mem["facts"][-5:])) # Last 5 facts only

    # History Search Section - Disabled by default to reduce verbosity
    # Uncomment if you want history search enabled
    # if user_query:
    #     history_hits = search_history(user_query, limit=3)
    #     if history_hits:
    #         context.append("Relevant past exchanges:\n" + "\n".join(history_hits))

    return "\n".join(context) if context else ""

def save_session_history(session_history, session_start_time):
    """Save the current session conversation to a timestamped file"""
    import time
    
    if not session_history:
        return
    
    sessions_dir = os.path.join("memory", "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    
    filename = f"session_{session_start_time}.txt"
    filepath = os.path.join(sessions_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"JARVIS Conversation Session\n")
        f.write(f"Started: {session_start_time}\n")
        f.write("=" * 60 + "\n\n")
        
        for role, text in session_history:
            f.write(f"{role}: {text}\n\n")
        
        f.write("=" * 60 + "\n")
        f.write(f"Session ended: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"💾 Session saved to: {filepath}")


