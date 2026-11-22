# MojeAI - Projektový status a plán (k 1. 11. 2026)

## 🎯 Vize projektu
Portable AI asistent ("obytňák"), který běží z jedné složky (flashdisk/server). Není to konkurence Ollamy, ale orchestration vrstva, která přidává:
- Dlouhodobou paměť (vektorová DB + textové zálohy).
- Rozdělení do projektů (oddělený kontext).
- AI nástroje (AI si sama rozhodne, co si uložit, umí číst a bezpečně editovat soubory se zálohou).
- Hybridní režim (lokální model pro běžné věci, cloud pro složité).

## ✅ Co je HOTOVO
1. **Fáze 0 (Git):** Repozitář na GitHubu (`v0.1-original`), `.gitignore`, `kontrola_klicu.py`.
2. **Fáze 1 (Refaktor):** Rozpad monolitického `app.py` na moduly (`core/`, `routes/`, `static/`).
3. **Fáze 2 (Lehká verze):** Odstranění těžkého `torch` a `chromadb`. Paměť běží na SQLite, embeddings přes `llama-cpp`.
4. **Fáze 2.5 (Portable + UX):**
    - Embedded Python 3.12.3 (`python/python.exe`).
    - Funkční UI (skrývací panel, opravené ukládání klíčů, **Markdown**).
    - Funkční internet (Open-Meteo pro počasí, DDG pro zprávy) s triggerem `//` pro vynucené hledání.
    - Nahrávání souborů (PDF, TXT) přes UI.
    - Detekce GPU (Windows + Linux).
    - Integrace Ollamy jako volitelného GPU backendu.

## ⚠️ Aktuální známé problémy (k opravě)
1. **Chyba SQLite ve vláknech:** V `core/memory.py` chybí `check_same_thread=False`. Způsobuje to chybu paměti při odesílání zpráv.
2. **Zacyklení lokálních GGUF modelů:** `llama-cpp-python` neumí chat templates. Pro Qwen3 a podobné modely je lepší použít Ollamu.
3. **Zmatek v modelech:** Uživatel má ve složce `OpenEuroLLM...` omylem nahraný soubor Gemma-12B, který je pro jeho hardware moc velký. Je třeba v UI vybrat menší model (Qwen3-8B, Phi-3.5).
4. **Výběr složky:** Tkinter dialog nebude fungovat na serveru (bez GUI). Cesta se musí psát ručně.

## 🚀 Co následuje (Fáze 3 - Jádro hodnoty)
1. **Projekty:** Přidání konceptu "Projektů" (oddělené paměti, složky, kontext).
2. **AI Nástroje (Function Calling):** AI dostane schopnost `zapamatuj_si()`, `precti_soubor()`, `zapis_do_souboru()`.
3. **Bezpečná editace:** Vynucená záloha před zápisem a potvrzovací dialog v UI.

## 🛠️ Struktura klíčových souborů
- `app.py` - Start aplikace
- `config.py` - Cesty a konfigurace
- `core/memory.py` - Paměť (SQLite + GGUF)
- `core/providers.py` - AI providery (Cloud, Ollama, GGUF)
- `routes/` - API endpointy
- `static/app.js` - Frontend logika
- `python/` - Portable Python
- `modely/` - GGUF modely
- `pamet/` - Textové zálohy paměti

## 🔧 Okamžité kroky k opravě:
1. V `core/memory.py` najít `sqlite3.connect(self.db_path)` a přepsat na `sqlite3.connect(self.db_path, check_same_thread=False)`.
2. Restartovat server.
3. V UI (v selectu modelů) vybrat menší model, např. `Qwen3-8B-Q8_0` nebo `Phi-3
