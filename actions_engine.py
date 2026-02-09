# actions_engine.py

import os
import subprocess
import re

# Mapping of common software names to their executable names or paths
# Values can be strings (paths/exes), lists (exe + arguments), or URI protocols
SOFTWARE_MAPPING = {
    "autocad": r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe",
    "civil 3d": [r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe", "/product", "C3D", "/language", "en-US"],
    "autocad civil 3d": [r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe", "/product", "C3D", "/language", "en-US"],
    "solidworks": r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    "solidwork": r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    "whatsapp": "whatsapp:", # UWP Protocol
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "excel": "excel.exe",
    "word": "winword.exe",
    "powerpoint": "powerpnt.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "vlc": "vlc.exe",
    "spotify": "spotify.exe",
    "browser": "chrome.exe",  # Default browser
    "code": "code.exe",       # VS Code
    "visual studio code": "code.exe",
}

def open_software(app_name):
    """
    Attempts to open a software application by name.
    """
    app_name_lower = app_name.lower().strip()
    
    # Check mapping
    target_data = SOFTWARE_MAPPING.get(app_name_lower, app_name_lower)
    
    # 0. Check if it's a protocol (ends with :)
    if isinstance(target_data, str) and target_data.endswith(":"):
        try:
            print(f"⚙️ Action: Starting protocol '{target_data}'")
            os.system(f'start {target_data}')
            return True
        except Exception as e:
            print(f"  - Protocol failed: {e}")

    # Split target into exe and args
    if isinstance(target_data, list):
        exe_path = target_data[0]
        args = target_data[1:]
    else:
        exe_path = target_data
        args = []
    
    print(f"⚙️ Action: Attempting to open '{app_name}' (Target: {exe_path})")
    
    # Attempt 1: os.startfile (doesn't support args directly easily, so we use it for plain paths)
    if not args:
        try:
            print(f"  - Trying os.startfile(r'{exe_path}')...")
            os.startfile(exe_path)
            return True
        except Exception:
            pass

    # Attempt 2: subprocess.Popen (best for args and paths with spaces)
    try:
        if args:
            full_command = [exe_path] + args
            print(f"  - Trying subprocess.Popen({full_command})...")
            subprocess.Popen(full_command)
        else:
            print(f"  - Trying subprocess.Popen(r'{exe_path}')...")
            quoted_exe = f'"{exe_path}"' if " " in exe_path else exe_path
            subprocess.Popen(quoted_exe, shell=True)
        return True
    except Exception as e:
        print(f"  - Subprocess failed: {e}")

    # Final attempt: direct shell start (handles some Windows aliases)
    try:
        quoted_name = f'"{app_name_lower}"' if " " in app_name_lower else app_name_lower
        print(f"  - Trying system start {quoted_name}...")
        if " " in app_name_lower:
            os.system(f'start "" {quoted_name}')
        else:
            os.system(f'start {quoted_name}')
        return True
    except:
        pass

    print(f"❌ Failed to open {app_name}")
    return False

def execute_action(action_string):
    """
    Parses and executes an action string like '[[ACTION: OPEN_APP, "app_name"]]'.
    Returns a status message.
    """
    # Regex to extract action and parameters (handles multiple params)
    # format: [[ACTION: TYPE, "param1", "param2", ...]]
    match = re.search(r'\[\[ACTION:\s*(\w+)(.*?)]\]', action_string)
    if not match:
        return "No action found."

    action_type = match.group(1).upper()
    params_str = match.group(2)
    params = re.findall(r'"(.*?)"', params_str)

    if action_type == "OPEN_APP":
        param = params[0] if params else ""
        success = open_software(param)
        if success:
            return f"Successfully initiated opening of {param}."
        else:
            return f"Could not find or open {param}, sir."
    
    elif action_type == "CALL":
        name = params[0] if params else "someone"
        print(f"⚙️ Action: Initiating call to {name}")
        # Try to open WhatsApp or Phone app
        try:
            # We can't deep link to a specific call easily without a phone number,
            # but we can open the app.
            os.system("start whatsapp:")
            return f"Opening WhatsApp to call {name} for you, sir."
        except:
            return f"Failed to initiate call to {name}."

    elif action_type == "EMAIL":
        recipient = params[0] if params else ""
        subject = params[1] if len(params) > 1 else ""
        print(f"⚙️ Action: Draft email to {recipient}")
        try:
            os.system(f'start mailto:{recipient}?subject={subject}')
            return f"Opening your email client to message {recipient}."
        except:
            return f"Failed to open email client."
    
    return f"Unknown action type: {action_type}"

if __name__ == "__main__":
    # Test
    print(execute_action('[[ACTION: OPEN_APP, "whatsapp"]]'))
    print(execute_action('[[ACTION: EMAIL, "test@example.com", "Hello from Jarvis"]]'))
