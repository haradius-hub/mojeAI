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
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = os.path.join(BASE_DIR, "python", "python.exe")
SERVER_URL = "http://127.0.0.1:5000/"
STARTUP_TIMEOUT = 60


def cekej_na_server(server):
    """Pocka, az Flask server skutecne odpovida, nebo zjisti chybu pri startu."""
    print("Cekam, az server zacne odpovidat...", flush=True)
    deadline = time.monotonic() + STARTUP_TIMEOUT

    while time.monotonic() < deadline:
        return_code = server.poll()
        if return_code is not None:
            print("\n[CHYBA] Proces serveru se ukoncil behem startu.")
            print(f"Navratovy kod: {return_code}")
            return False

        try:
            with urllib.request.urlopen(SERVER_URL, timeout=2) as response:
                if response.status < 500:
                    print("[OK] Server odpovida.", flush=True)
                    return True
        except urllib.error.HTTPError as error:
            # HTTP odpoved znamena, ze server nasloucha; chyba 5xx ale
            # znamena problem pri obsluze uvodni stranky.
            if error.code < 500:
                print("[OK] Server odpovida.", flush=True)
                return True
            print(f"\n[CHYBA] Server odpovida chybou HTTP {error.code}.")
            return False
        except (urllib.error.URLError, TimeoutError, OSError):
            pass

        time.sleep(0.5)

    print(f"\n[CHYBA] Server nezacal odpovidat do {STARTUP_TIMEOUT} sekund.")
    return False


def main():
    print("=" * 60)
    print("   MOJEAI - Portable AI Assistant")
    print("=" * 60)

    if not os.path.exists(PYTHON_EXE):
        print("[CHYBA] Chybi portable Python.")
        print("Spust nejprve 'setup_portable.bat'.")
        input("Stiskni Enter pro ukonceni...")
        sys.exit(1)

    if not os.path.exists(os.path.join(BASE_DIR, "modely", "nomic-embed-text-v1.5.Q8_0.gguf")):
        print("[VAROVANI] Chybi embedding model.")
        print("Aplikace muze bezet, ale semanticka pamet nebude dostupna.")

    print("\nSpoustim server...", flush=True)
    server = subprocess.Popen([PYTHON_EXE, "app.py"], cwd=BASE_DIR)

    try:
        if not cekej_na_server(server):
            print("\nProhlizec neoteviram, protoze server neni pripraven.")
            print("Vystup serveru vyse obsahuje podrobnosti o pripadne chybe.")
            if server.poll() is None:
                print("Serverovy proces stale bezi. Stiskni Ctrl+C pro jeho ukonceni.")
                server.wait()
            else:
                input("Stiskni Enter pro ukonceni...")
            sys.exit(1)

        print("\nOteviram prohlizec...", flush=True)
        webbrowser.open("http://localhost:5000")

        print("\nMojeAI bezi. Pro ukonceni stiskni Ctrl+C.", flush=True)
        server.wait()

    except KeyboardInterrupt:
        print("\nUkoncuji server...", flush=True)
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    main()
