# memory_engine.py
# Clean, non-nesting, persistent memory + profile + conversation
# Creates folders and files if missing, self-heals on corrupt JSON.

import json
import os
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
PROFILE_FILE = os.path.join(BASE_DIR, "profile.json")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
CONVO_FILE = os.path.join(BASE_DIR, "conversation.json")

# Ensure dirs exist once
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

def _load_json(path: str, default: Any) -> Any:
    """Load JSON; if missing or corrupt, write default and return it."""
    try:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Self-heal corrupt files
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default

def _save_json(path: str, data: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

class MemoryEngine:
    """Keeps profile, facts, and conversation in simple, stable shapes."""
    def __init__(self):
        self._profile_default = {"name": "User", "timezone": "America/Regina"}
        self._memory_default  = {"facts": {}}                 # <--- dict of key -> value
        self._convo_default   = []                            # <--- list of {"user": "...", "ai": "..."}

    # -------- Profile --------
    def load_profile(self) -> Dict[str, Any]:
        return _load_json(PROFILE_FILE, self._profile_default)

    def save_profile(self, profile: Dict[str, Any]) -> None:
        _save_json(PROFILE_FILE, profile)

    # -------- Facts / Memory --------
    def load_memory(self) -> Dict[str, Any]:
        data = _load_json(MEMORY_FILE, self._memory_default)
        # Normalize shape if someone hand-edited to a list, etc.
        if not isinstance(data, dict):
            data = self._memory_default
            _save_json(MEMORY_FILE, data)
        if "facts" not in data or not isinstance(data["facts"], dict):
            data["facts"] = {}
            _save_json(MEMORY_FILE, data)
        return data

    def save_memory_fact(self, key: str, value: str) -> None:
        """Add or update a single fact (no nesting)."""
        data = self.load_memory()
        data["facts"][key.strip()] = value.strip()
        _save_json(MEMORY_FILE, data)

    # -------- Conversation --------
    def load_conversation(self) -> List[Dict[str, str]]:
        conv = _load_json(CONVO_FILE, self._convo_default)
        if not isinstance(conv, list):
            conv = self._convo_default
            _save_json(CONVO_FILE, conv)
        return conv

    def append_conversation(self, user_text: str, ai_text: str) -> None:
        conv = self.load_conversation()
        conv.append({"user": user_text, "ai": ai_text})
        _save_json(CONVO_FILE, conv)

    # -------- Context builder --------
    def build_context(self, user_input: str, max_history: int = 10) -> str:
        profile = self.load_profile()
        memory  = self.load_memory()
        convo   = self.load_conversation()

        parts = []
        parts.append(f"[PROFILE] name={profile.get('name','User')} timezone={profile.get('timezone','America/Regina')}")
        if memory.get("facts"):
            facts_txt = "; ".join(f"{k}={v}" for k, v in memory["facts"].items())
            parts.append(f"[FACTS] {facts_txt}")
        if convo:
            tail = convo[-max_history:]
            conv_txt = " | ".join(f"You: {c['user']} || Jarvis: {c['ai']}" for c in tail if "user" in c and "ai" in c)
            parts.append(f"[HISTORY last={len(tail)}] {conv_txt}")
        parts.append(f"[USER] {user_input}")
        return "\n".join(parts)
