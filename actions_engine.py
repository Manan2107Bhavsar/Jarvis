# actions_engine.py

import os
import subprocess
import re
import threading
import time
from screeninfo import get_monitors

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

def get_monitor_bounds(monitor_index):
    """Returns (x, y, w, h) for a given monitor index (1-indexed)."""
    monitors = get_monitors()
    if not monitors:
        return None
    
    # Defaults to primary if index is out of range
    idx = max(0, min(monitor_index - 1, len(monitors) - 1))
    m = monitors[idx]
    return (m.x, m.y, m.width, m.height)

def move_window_to_monitor(app_name, monitor_index):
    """
    Polls for a window associated with app_name and moves it to the target monitor.
    Uses a 7-second timeout.
    """
    if not win32gui:
        print("⚠️ win32gui not available. Skipping window move.")
        return

    bounds = get_monitor_bounds(monitor_index)
    if not bounds:
        return

    target_x, target_y, target_w, target_h = bounds
    app_name_lower = app_name.lower()
    
    # Polling for up to 20 seconds to be safe (it stops as soon as found)
    start_time = time.time()
    found = False
    
    while time.time() - start_time < 20:
        def callback(hwnd, extra):
            nonlocal found
            # Filter for visible windows with titles
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    title_lower = title.lower()
                    
                    # Exclusion list for add-ons/splash screens
                    if "_fs" in title_lower or "splash" in title_lower:
                        return True
                    
                    # Check for app name or common variations
                    is_match = False
                    if app_name_lower in title_lower:
                        # Extra check for solidworks to ensure it's the main app
                        if app_name_lower == 'solidworks':
                            # Main window usually has "Premium", "Standard", "Professional" or the SP version
                            if "premium" in title_lower or "sp1" in title_lower or "sp0" in title_lower:
                                is_match = True
                            # Fallback if "sldworks" is found but no specific version string yet
                            elif "sldworks" in title_lower and len(title) > 10:
                                is_match = True
                        else:
                            is_match = True
                    elif app_name_lower == 'solidworks' and 'sldworks' in title_lower:
                        # Catch sldworks if app_name_lower is 'solidworks'
                        is_match = True
                    
                    if is_match:
                        print(f"🎯 Found window '{title}' for {app_name}. Moving to monitor {monitor_index}...")
                        # Restore/Show if minimized
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        # Move window
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, target_x, target_y, target_w, target_h, win32con.SWP_SHOWWINDOW)
                        # Maximize
                        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                        found = True
                        return False # Stop enumeration
            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception:
            pass 

        if found:
            break
        time.sleep(0.5) 

    if not found:
        print(f"⏳ Timeout: Could not find main window for '{app_name}' within 20 seconds.")

# Mapping of common software names to their executable names or paths
# Values can be strings (paths/exes), lists (exe + arguments), or URI protocols
SOFTWARE_MAPPING = {
    "autocad": r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe",
    "civil 3d": [r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe", "/product", "C3D", "/language", "en-US"],
    "autocad civil 3d": [r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe", "/product", "C3D", "/language", "en-US"],
    "solidworks": r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    "solidwork": r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    "revit": r"C:\Program Files\Autodesk\Revit 2026\Revit.exe",
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

def open_software(app_name, monitor=None):
    """
    Attempts to open a software application by name.
    Optional monitor index (1, 2, etc.)
    """
    app_name_lower = app_name.lower().strip()
    
    # Check mapping
    target_data = SOFTWARE_MAPPING.get(app_name_lower, app_name_lower)
    
    # 0. Check if it's a protocol (ends with :)
    if isinstance(target_data, str) and target_data.endswith(":"):
        try:
            print(f"⚙️ Action: Starting protocol '{target_data}'")
            os.system(f'start {target_data}')
            # Optional: Move to monitor (UWP apps can be tricky)
            if monitor:
                threading.Thread(target=move_window_to_monitor, args=(app_name, monitor), daemon=True).start()
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
    success = False
    if not args:
        try:
            print(f"  - Trying os.startfile(r'{exe_path}')...")
            os.startfile(exe_path)
            success = True
        except Exception:
            pass

    # Attempt 2: subprocess.Popen (best for args and paths with spaces)
    if not success:
        try:
            if args:
                full_command = [exe_path] + args
                print(f"  - Trying subprocess.Popen({full_command})...")
                subprocess.Popen(full_command)
            else:
                print(f"  - Trying subprocess.Popen(r'{exe_path}')...")
                quoted_exe = f'"{exe_path}"' if " " in exe_path else exe_path
                subprocess.Popen(quoted_exe, shell=True)
            success = True
        except Exception as e:
            print(f"  - Subprocess failed: {e}")

    # Final attempt: direct shell start (handles some Windows aliases)
    if not success:
        try:
            quoted_name = f'"{app_name_lower}"' if " " in app_name_lower else app_name_lower
            print(f"  - Trying system start {quoted_name}...")
            if " " in app_name_lower:
                os.system(f'start "" {quoted_name}')
            else:
                os.system(f'start {quoted_name}')
            success = True
        except:
            pass

    if success:
        if monitor:
            print(f"🚀 Monitor {monitor} specified. Starting placement thread...")
            threading.Thread(target=move_window_to_monitor, args=(app_name, monitor), daemon=True).start()
        return True

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
    # Extract params - handle both "quoted" and unquoted params separated by commas
    params = []
    # This splits by comma, then strips whitespace and quotes
    raw_params = params_str.split(',')
    for p in raw_params:
        p = p.strip()
        if not p: continue
        # Remove surrounding quotes if present
        if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
            p = p[1:-1]
        params.append(p)

    if action_type == "OPEN_APP":
        param = params[0] if params else ""
        monitor = int(params[1]) if len(params) > 1 and params[1].isdigit() else None
        success = open_software(param, monitor)
        if success:
            msg = f"Successfully initiated opening of {param}"
            if monitor:
                msg += f" on monitor {monitor}"
            return msg + "."
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
