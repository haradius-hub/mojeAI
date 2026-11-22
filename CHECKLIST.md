# MojeAI - Projektový checklist (Stav k 31. 10. 2026)

## ✅ Co už máme hotové
1. **Fáze 0 (Git)**: Původní kód je zazálohovaný na GitHubu jako `v0.1-original`. Je nastavený `.gitignore` a `kontrola_klicu.py`.
2. **Fáze 1 (Refaktor)**: Monolitický `app.py` je rozdělen do modulů:
   - `app.py` (bootstrap)
   - `config.py` (cesty)
   - `core/memory.py` (paměť)
   - `core/providers.py` (AI modely)
   - `routes/` (API endpointy)
   - `static/` (JS a CSS oddělené od HTML)
3. **Cesta B (Lehká verze)**: Zbavili jsme se `chromadb` a `torch`.
   - Paměť běží na `sqlite-vec` (jednosouborová DB).
   - Embeddings běží přes `llama-cpp-python` (model `nomic-embed-text`).
   - Vytvořili jsme `setup_portable.bat` pro Embedded Python.
   - Vytvořili jsme `run.py`, který spouští lokální Python.

## 🔧 Aktuální problém (vyřešeno)
- **Chyba**: `ModuleNotFoundError: No module named 'config'`
- **Příčina**: Embedded Python neviděl do aktuální složky.
- **Řešení**: Upravit `python/python312._pth` (přidat tečku na samostatný řádek) a upravit `app.py` (vynutit `sys.path`).

## 🚀 Co následuje (Fáze 3 - Projekty a AI nástroje)
Až se nám podaří aplikaci spustit, dalším krokem bude:
1. **Projekty**: Přidat do UI možnost vytvořit "Projekt" (např. "Web", "Kód", "Osobní"). Každý projekt bude mít vlastní paměť (oddělené DB nebo složky).
2. **AI Nástroje (Function Calling)**: AI dostane schopnost:
   - `zapamatuj_si(text)` - rozhodne se, co si uložit do dlouhodobé paměti.
   - `precti_soubor(cesta)` - přečte soubor z povolené složky.
   - `zapis_do_souboru(cesta, text)` - **bezpečně** zapíše do souboru. Vytvoří zálohu do `zalohy/` a vyžádá si potvrzení od uživatele v UI.
3. **UI Vylepšení**: Přidat markdown do chatu, streaming odpovědí a potvrzovací dialogy.

## 🛠️ Co dělat, když se to rozbije
- **Chyba `sqlite_vec`**: Zkontroluj, že máš v Pythonu nainstalováno `pip install sqlite-vec`.
- **Chyba `llama_cpp`**: Ujisti se, že `pip install llama-cpp-python` proběhl úspěšně (v `setup_portable.bat`).
- **Paměť nefunguje**: Ujisti se, že máš v `modely/` stažený soubor `nomic-embed-text-v1.5.Q8_0.gguf`. Pokud ne, spusť `python\python.exe stahni_model.py`.

## 📂 Struktura klíčových souborů
- `app.py` - start aplikace
- `config.py` - konfigurace cest
- `core/memory.py` - stará se o ukládání a hledání v paměti (SQLite)
- `core/providers.py` - připojení k AI (Gemini, DeepSeek, lokální GGUF)
- `routes/` - API
- `static/` - frontend (app.js, style.css)
- `templates/index.html` - hlavní stránka
- `python/` - portable Python
- `modely/` - modely (GGUF)
- `pamet/` - textové soubory paměti (zálohy)
- `data/` - SQL
