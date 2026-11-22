#!/usr/bin/env bash
set -e

# Spousti MojeAI v izolovanem virtualnim prostredi.
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[CHYBA] Python 3 nebyl nalezen."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Vytvarim virtualni prostredi .venv..."
    if ! python3 -m venv .venv; then
        echo "[CHYBA] Vytvoreni virtualniho prostredi selhalo."
        echo "Na Debianu/Ubuntu doinstaluj balik python3-venv."
        exit 1
    fi
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Instaluji/overuji zavislosti..."
python -m pip install -r requirements.txt

echo "Spoustim MojeAI na http://localhost:5000 ..."
exec python app.py
