# MojeAI – aktuální stav projektu

Tento dokument popisuje stav ověřený kontrolou zdrojového kódu v pracovní větvi `cleanup/repository-audit`. Nejde o potvrzení, že aplikace byla v tomto kroku spuštěna nebo otestována.

## Vize

MojeAI má být přenositelná aplikační a orchestrace vrstva pro různé modely – cloudové i lokální. Ollama zůstává samostatným backendem, nikoli konkurentem, kterého by projekt měl znovu implementovat.

Dlouhodobým cílem je osobní AI pracovní prostředí s historií, dlouhodobou a projektovou pamětí, skutečným tool calling a bezpečnou prací se soubory. Současný kód představuje pouze základ této vize.

## Co je v aktuálním kódu implementováno

### Aplikace a rozhraní
- Flask aplikace má modulární strukturu: `app.py`, `config.py`, `core/`, `routes/`, `static/` a `templates/`.
- Webové rozhraní nabízí chat, výběr dostupného modelu, nastavení systémového promptu, API klíčů, internetu a parametrů lokálního modelu.
- Odpovědi se zobrazují po dokončení požadavku; streaming není implementován.
- Frontend vykresluje Markdown pomocí knihovny Marked načítané z CDN.

### Modely a poskytovatelé
- Implementováni jsou poskytovatelé Gemini, DeepSeek, OpenAI a Claude.
- Kód umí vyhledat lokální GGUF soubory a předat je do `llama-cpp-python`.
- Kód umí načíst seznam modelů z lokálního API Ollamy a odeslat jí požadavek.
- GPU informace se zjišťují orientačně. Samotná detekce GPU nezajišťuje funkční akceleraci.

### Paměť
- `core/memory.py` používá SQLite databázi `data/pamet.db`.
- Textové záznamy se ukládají také jako soubory do `pamet/`.
- Sémantické vyhledávání počítá embeddingy přes `llama-cpp-python` a model `nomic-embed-text-v1.5.Q8_0.gguf`.
- Paměť není totéž co historie konverzací. Kompletní seznam chatů, jejich opětovné otevírání a vyhledávání v historii implementovány nejsou.

### Projekty
- `core/projects.py` a `routes/projects.py` implementují databázovou evidenci projektů, popisů, instrukcí a povolených složek s oprávněním read/read_write.
- Jde o backendové API a evidenci oprávnění. Projekty zatím nejsou propojeny s chatovacím rozhraním ani s oddělenými paměťmi.
- Připojení složky samo o sobě nezpřístupňuje její obsah modelu.

### Internet a soubory
- Chatový endpoint obsahuje základní vyhledávání přes DuckDuckGo a zvláštní větev pro počasí přes Open-Meteo.
- Uživatel může v chatu vynutit hledání prefixem `//`.
- Endpoint přijímá PDF, TXT, MD, PY a CSV; obsah je vložen do konkrétního požadavku. Nejde o trvalou knihovnu dokumentů.

### Provoz a bezpečnost
- `setup_portable.bat` připravuje Embedded Python 3.12.3 a instaluje základní závislosti včetně CPU varianty `llama-cpp-python`.
- `run.py` spouští aplikaci přes `python/python.exe`.
- `spustit.sh` a `spustit_cpu.bat` používají systémový Python.
- Flask server naslouchá na `127.0.0.1:5000`; aplikace odmítá požadavky s jiným Host a kontroluje Origin u změnových požadavků. Přihlášení implementováno není.
- API klíče se ukládají do lokálních souborů `api_klic/*.txt`, které ignoruje Git.

## Co není implementováno

- Kompletní historie konverzací, její vyhledávání, procházení a opětovné otevření.
- Modelové function/tool calling, registr nástrojů a vykonávání volání podle rozhodnutí modelu.
- AI čtení souborů z povolených projektových složek.
- Bezpečné zápisy souborů, potvrzování uživatelem a automatické zálohy před změnou.
- Projektově oddělený kontext a paměť.
- Uživatelské rozhraní pro správu projektů.
- Plnohodnotné řízení oprávnění a přihlašování pro více uživatelů.
- Ověřená a jednotná instalace GPU variant pro Windows/Linux.

## Známé technické nedostatky k prověření

1. `spustit_gpu.bat` instaluje zastaralé balíčky včetně ChromaDB, Torch a Transformers, přestože aktuální kód používá jinou architekturu. Nelze jej považovat za podporovanou instalační cestu.
2. `requirements.txt` neobsahuje `llama-cpp-python`. Portable instalační skript jej přidává zvlášť; systémová instalace jej musí doplnit ručně, pokud má fungovat GGUF a sémantická paměť.
3. Linuxový launcher instaluje pouze `requirements.txt`; neinstaluje `llama-cpp-python` ani embedding model.
4. Soubory `api_klic/*.txt.example` jsou prázdné; návod je proto veden v `api_klic/README.md`.
5. Je třeba prověřit chování paměti při chybějícím embedding modelu a při souběžných požadavcích.
6. Automatické testy a reprodukovatelný testovací postup zatím nejsou v repozitáři doloženy.

## Doporučené pořadí další práce

1. Dokončit dokumentaci a sjednotit popis instalačních cest.
2. Opravit a ověřit Windows CPU/portable/GPU spouštění; GPU režim nepovažovat za funkční, dokud nebude skutečně otestován.
3. Prověřit ukládání a vyhledávání paměti včetně chybových stavů.
4. Připravit minimální automatické testy backendu a bezpečnostních omezení.
5. Teprve poté pokračovat v návrhu historie konverzací, projektového kontextu a tool calling.
6. Historické soubory odstraňovat až po porovnání a archivaci.

## Poznámka k ověření

Tento status vychází z kontroly zdrojových souborů. V rámci dokumentační etapy nebyla aplikace spuštěna, nebyla ověřena instalace závislostí ani nebyly provedeny runtime testy.
