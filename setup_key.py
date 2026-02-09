import os
import shutil
import sys

def setup_key():
    print("================================================================")
    print("   Jarvis Google Cloud Key Setup Helper")
    print("================================================================")
    print("This script will help you copy your Google Cloud JSON key file")
    print("to the correct location so Jarvis can use it.")
    print("================================================================")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_filename = "jarvis-470021-764ade9fe25d.json"
    target_path = os.path.join(current_dir, target_filename)
    
    if os.path.exists(target_path):
        print(f"\n✅ Key file already exists at:\n{target_path}")
        choice = input("\nDo you want to overwrite it? (y/n): ").lower()
        if choice != 'y':
            print("Exiting...")
            return

    print(f"\nPlease enter the full path to your '{target_filename}' file.")
    print("You can drag and drop the file here and press Enter.")
    
    source_path = input("\nPath: ").strip()
    
    # Remove quotes if user dragged and dropped
    if source_path.startswith('"') and source_path.endswith('"'):
        source_path = source_path[1:-1]
        
    if not os.path.exists(source_path):
        print(f"\n❌ Error: File not found at:\n{source_path}")
        print("Please check the path and try again.")
        input("\nPress Enter to exit...")
        return
        
    try:
        shutil.copy2(source_path, target_path)
        print(f"\n✅ Success! Key file copied to:\n{target_path}")
        print("\nYou can now restart Jarvis.")
    except Exception as e:
        print(f"\n❌ Error copying file: {e}")
        
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    setup_key()
