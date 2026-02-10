# actions_engine.py

import os
import subprocess
import re
import threading
import time
import json
import shutil
from screeninfo import get_monitors

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

def find_app_with_powershell(app_name):
    """
    Uses PowerShell to find an app by its friendly name (Start Menu name).
    Returns the AppID if found, else None.
    """
    try:
        # PowerShell command to find the app
        # Match name case-insensitively.
        ps_cmd = f"Get-StartApps | Where-Object {{ $_.Name -match '{app_name}' }} | Select-Object -First 1 Name, AppID | ConvertTo-Json"
        full_cmd = ["powershell", "-Command", ps_cmd]
        
        output = subprocess.check_output(full_cmd, stderr=subprocess.STDOUT).decode('utf-8').strip()
        if output:
            data = json.loads(output)
            if isinstance(data, dict):
                print(f"  - PowerShell found: {data.get('Name')} -> {data.get('AppID')}")
                return data.get('AppID')
    except Exception as e:
        print(f"  - PowerShell discovery failed for '{app_name}': {e}")
    return None

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
    """
    if not win32gui:
        print("⚠️ win32gui not available. Skipping window move.")
        return

    bounds = get_monitor_bounds(monitor_index)
    if not bounds:
        return

    target_x, target_y, target_w, target_h = bounds
    app_name_lower = app_name.lower()
    
    # Polling for up to 20 seconds to be safe
    start_time = time.time()
    found = False
    
    while time.time() - start_time < 20:
        def callback(hwnd, extra):
            nonlocal found
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    title_lower = title.lower()
                    
                    if "_fs" in title_lower or "splash" in title_lower:
                        return True
                    
                    is_match = False
                    if app_name_lower in title_lower:
                        if app_name_lower == 'solidworks':
                            if any(x in title_lower for x in ["premium", "sp1", "sp0", "standard", "professional"]):
                                is_match = True
                            elif "sldworks" in title_lower and len(title) > 10:
                                is_match = True
                        else:
                            is_match = True
                    elif app_name_lower == 'solidworks' and 'sldworks' in title_lower:
                        is_match = True
                    
                    if is_match:
                        print(f"🎯 Found window '{title}' for {app_name}. Moving to monitor {monitor_index}...")
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, target_x, target_y, target_w, target_h, win32con.SWP_SHOWWINDOW)
                        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                        found = True
                        return False
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

SOFTWARE_MAPPING = {
    "autocad": r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe",
    "civil 3d": [r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe", "/product", "C3D", "/language", "en-US"],
    "autocad civil 3d": [r"C:\Program Files\Autodesk\AutoCAD 2026\acad.exe", "/product", "C3D", "/language", "en-US"],
    "solidworks": r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    "solidwork": r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
    "revit": r"C:\Program Files\Autodesk\Revit 2026\Revit.exe",
    "whatsapp": "whatsapp:",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "excel": "excel.exe",
    "word": "winword.exe",
    "powerpoint": "powerpnt.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "vlc": "vlc.exe",
    "spotify": "spotify.exe",
    "browser": "chrome.exe",
    "code": "code.exe",
    "visual studio code": "code.exe",
}

def open_software(app_name, monitor=None):
    """
    Attempts to open a software application with robust Windows discovery.
    """
    app_name_lower = app_name.lower().strip()
    target_data = SOFTWARE_MAPPING.get(app_name_lower, app_name_lower)
    
    # 0. Protocol Check
    if isinstance(target_data, str) and target_data.endswith(":"):
        try:
            os.system(f'start {target_data}')
            if monitor:
                threading.Thread(target=move_window_to_monitor, args=(app_name, monitor), daemon=True).start()
            return True
        except: pass

    # 1. PowerShell Discovery Fallback (Permanent Solution for Apps with Spaces)
    app_id = None
    if target_data == app_name_lower and " " in app_name_lower:
        print(f"🔍 Discovery: Searching for '{app_name}' via PowerShell...")
        app_id = find_app_with_powershell(app_name_lower)
        if app_id:
            target_data = f"shell:AppsFolder\\{app_id}"

    # 2. Determine target
    if isinstance(target_data, list):
        exe_path = target_data[0]
        args = target_data[1:]
    else:
        exe_path = target_data
        args = []
    
    print(f"⚙️ Action: Opening '{app_name}' (Target: {exe_path})")
    
    success = False
    # Attempt A: Direct start / shell execution
    try:
        if not args:
            # shell:AppsFolder or registered EXEs
            if exe_path.startswith("shell:") or " " not in exe_path:
                os.system(f'start "" {exe_path}')
            else:
                os.startfile(exe_path)
            success = True
    except: pass

    # Attempt B: Subprocess for complex commands
    if not success:
        try:
            cmd = [exe_path] + args if args else (["cmd", "/c", "start", "", exe_path] if " " in exe_path else [exe_path])
            subprocess.Popen(cmd, shell=True if not args else False)
            success = True
        except Exception as e:
            print(f"  - Launch failed: {e}")

    if success:
        if monitor:
            threading.Thread(target=move_window_to_monitor, args=(app_name, monitor), daemon=True).start()
        return True

    return False

def execute_action(action_string):
    match = re.search(r'\[\[ACTION:\s*(\w+)(.*?)]\]', action_string)
    if not match: return "No action found."

    action_type = match.group(1).upper()
    params_str = match.group(2)
    params = [p.strip().strip('"\'') for p in params_str.split(',') if p.strip()]

    if action_type == "OPEN_APP":
        param = params[0] if params else ""
        monitor = int(params[1]) if len(params) > 1 and params[1].isdigit() else None
        if open_software(param, monitor):
            return f"Opening {param}" + (f" on monitor {monitor}." if monitor else ".")
        return f"Could not open {param}."
    
    elif action_type == "CALL":
        name = params[0] if params else "someone"
        print(f"⚙️ Action: Initiating call to {name}")
        try:
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
    
    return f"Unknown action: {action_type}"
