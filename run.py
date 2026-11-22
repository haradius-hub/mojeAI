#!/usr/bin/env python3
"""
Univerzalni launcher pro MojeAI.
Pouziva lokalni portable Python ve slozce 'python/'.
"""
import os
import sys
import subprocess
import time
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(BASE_DIR, "python", "python.exe")

def main():
    print("=" * 60)
    print("   MOJEAI - Portable AI Assistant")
    print("=" * 60)
    
    if not os.path.exists(PYTHON_EXE):
        print("❌ Chyba: Chybi portable Python.")
        print("   Spust nejprve 'setup_portable.bat'.")
        sys.exit(1)
        
    if not os.path.exists(os.path.join(BASE_DIR, "modely", "nomic-embed-text-v1.5.Q8_0.gguf")):
        print("⚠️  Varovani: Chybi embedding model.")
        print("   Spust: python\\python.exe stahni_model.py")
        print("   (Aplikace pobezi, ale pamet nebude fungovat.)")

    print("Spoustim server...")
    server = subprocess.Popen([PYTHON_EXE, "app.py"], cwd=BASE_DIR)
    
    time.sleep(3)
    print("\nOteviram prohlizec...")
    webbrowser.open("http://localhost:5000")
    
    try:
        server.wait()
    except KeyboardInterrupt:
        print("\nUkoncuji server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    main()
