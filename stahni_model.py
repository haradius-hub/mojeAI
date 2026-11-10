#!/usr/bin/env python3
"""
Stahne model nomic-embed-text-v1.5 (GGUF) pro embeddings.
Spusteni: python stahni_model.py
"""
import os
from huggingface_hub import hf_hub_download

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELY_DIR = os.path.join(BASE_DIR, "modely")
os.makedirs(MODELY_DIR, exist_ok=True)

print("Stahuji model nomic-embed-text-v1.5.Q8_0.gguf (muze to trvat chvilku)...")
try:
    cesta = hf_hub_download(
        repo_id="nomic-ai/nomic-embed-text-v1.5-GGUF",
        filename="nomic-embed-text-v1.5.Q8_0.gguf",
        local_dir=MODELY_DIR,
        local_dir_use_symlinks=False
    )
    print(f"✅ Model uspesne stazen do: {cesta}")
except Exception as e:
    print(f"❌ Chyba pri stahovani: {e}")
