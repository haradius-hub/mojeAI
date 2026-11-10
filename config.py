# config.py
import os
import json

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PAMET_DIR = os.path.join(BASE_DIR, "pamet")
    API_KLICE_DIR = os.path.join(BASE_DIR, "api_klic")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    MODELY_DIR = os.path.join(BASE_DIR, "modely")
    CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

    @classmethod
    def init_dirs(cls):
        for path in [cls.PAMET_DIR, cls.API_KLICE_DIR, cls.DATA_DIR, cls.MODELY_DIR]:
            os.makedirs(path, exist_ok=True)

    @classmethod
    def nacti(cls):
        vychozi = {
            "system_prompt": "Jsi užitečný asistent. Odpovídej česky, stručně a výstižně. Používej přirozenou češtinu bez zbytečných formalit.",
            "vychozi_model": "gemini",
            "pristupne_slozky": [],
            "internet": False,
            "smart_search": True,
            "max_vzpominek": 5,
            "pouzit_gpu": False,
            "gpu_vrstev": 25,
            "n_ctx": 2048,      # Výchozí velikost kontextu
            "n_threads": 4      # Výchozí počet vláken CPU
        }
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in vychozi.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception:
                pass
        return vychozi

    @classmethod
    def uloz(cls, config_data):
        with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)