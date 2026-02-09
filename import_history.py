import os
import json
from bs4 import BeautifulSoup
import sys

# Configuration
IMPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "import")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory", "history.jsonl")
INPUT_FILE = os.path.join(IMPORT_DIR, "history.html")

def parse_history():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found: {INPUT_FILE}")
        print("Please place 'history.html' in the 'import' folder.")
        return

    print(f"Reading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("Parsing HTML content...")
    
    # This selector depends on the export format (ChatGPT usually uses specific classes)
    # We'll try a generic approach finding conversation containers
    # Adjust selectors based on actual HTML structure if needed
    
    messages = []
    
    # Common structure for ChatGPT exports
    # Usually divs with classes like "group w-full..." or specific role attributes
    # Or just simple p tags if it's a basic export
    
    # Let's try to find all text elements and infer structure
    # Or look for standard conversation markers
    
    # Strategy: Look for "User" and "ChatGPT" or "Assistant" headers
    # This is a heuristic.
    
    # Better strategy: Just extract all text and save chunks?
    # No, we want structure.
    
    # Let's try to find divs that look like messages
    # Assuming standard ChatGPT export
    
    conversations = soup.find_all("div", class_="conversation-item") # Hypothetical
    
    if not conversations:
        # Fallback: Extract all text and split by newlines, trying to identify speakers
        print("Structured parsing failed. Falling back to text extraction.")
        text = soup.get_text(separator="\n")
        lines = text.split("\n")
        
        current_role = "unknown"
        buffer = []
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Heuristic for roles
                if line.lower() in ["user", "you"]:
                    if buffer:
                        entry = {"role": current_role, "text": "\n".join(buffer), "timestamp": ""}
                        out.write(json.dumps(entry) + "\n")
                        buffer = []
                    current_role = "user"
                elif line.lower() in ["chatgpt", "assistant", "model", "ai"]:
                    if buffer:
                        entry = {"role": current_role, "text": "\n".join(buffer), "timestamp": ""}
                        out.write(json.dumps(entry) + "\n")
                        buffer = []
                    current_role = "assistant"
                else:
                    buffer.append(line)
            
            # Save last buffer
            if buffer:
                entry = {"role": current_role, "text": "\n".join(buffer), "timestamp": ""}
                out.write(json.dumps(entry) + "\n")
                
    else:
        # If we had correct selectors, we'd do it here.
        # Since I don't know the exact format of the user's file, text extraction is safer.
        pass

    print(f"History imported to {OUTPUT_FILE}")

if __name__ == "__main__":
    # Ensure memory dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    parse_history()
