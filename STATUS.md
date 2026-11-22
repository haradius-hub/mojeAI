# MojeAI – aktuální stav projektu

Tento dokument popisuje stav zjištěný kontrolou zdrojového kódu v pracovní větvi `cleanup/repository-audit`. Úpravy spouštěcích skriptů a dokumentace byly zapsány, ale jejich běh na Windows ani Linuxu zatím nebyl prakticky otestován.

## Vize

MojeAI má být přenositelná aplikační a orchestrace vrstva pro různé modely – cloudové i lokální. Ollama zůstává samostatným backendem, nikoli konkurentem, kterého by projekt měl znovu implementovat.

Dlouhodobým cílem je osobní AI pracovní prostředí s historií, dlouhodobou a projektovou pamětí, skutečným tool calling a bezpečnou prací se soubory. Současný kód představuje pouze základ této vize.

## Implementované části

### Aplikace a modely
- Modulární Flask aplikace: `app.py`, `config.py`, `core/`, `routes/`, `static/` a `templates/`.
- Chatovací rozhraní a nastavení systémového promptu, modelu, API klíčů, internetu a parametrů lokálního modelu.
- Poskytovatelé Gemini, DeepSeek, OpenAI a Claude.
- Lokální GGUF modely přes `llama-cpp-python`.
- Připojení k lokálnímu API Ollamy a načtení seznamu modelů.
- Základní internetové vyhledávání a získání počasí.
- Přijetí PDF, TXT, MD, PY a CSV do konkrétního chatového požadavku.

### Paměť a projekty
- Dlouhodobá paměť používá SQLite databázi `data/pamet.db` a textové záznamy ve složce `pamet/`.
- Sémantické vyhledávání vyžaduje `llama-cpp-python` a model `nomic-embed-text-v1.5.Q8_0.gguf`.
- Backend eviduje projekty, popisy, instrukce a povolené složky. Projekty zatím nejsou propojené s chatem ani oddělenou pamětí.

### Provoz a bezpečnost
- Windows portable: Embedded Python 3.12.3, `setup_portable.bat` a `run.py`.
- Windows systémový Python: `spustit_cpu.bat`.
- Linux: `spustit.sh` vytváří a používá lokální `.venv`.
- Server naslouchá na `127.0.0.1:5000`; aplikace kontroluje lokální Host a Origin u změnových požadavků.
- API klíče se ukládají do lokálních souborů `api_klic/*.txt`, které ignoruje Git.

## Stav spouštěcích cest po úpravě

- `spustit.bat` nabízí portable Python (doporučený) a systémový Python (CPU).
- `setup_portable.bat` kontroluje chyby stahování a instalace základních závislostí; instalace `llama-cpp-python` je doplňková a při selhání vypíše upozornění.
- `spustit_cpu.bat` používá `python -m pip`, ověřuje instalaci závislostí a spouští server z adresáře projektu.
- `spustit_gpu.bat` je záměrně vypnutý, protože původní detekce GPU a instalace neodpovídaly aktuálnímu kódu.
- `spustit.sh` používá virtuální prostředí, aby se vyhnul instalaci balíčků do systémového Pythonu (např. Debian/Ubuntu s PEP 668).

Tyto body popisují obsah skriptů, nikoli potvrzené úspěšné spuštění na cílových operačních systémech.

## Co není implementováno

- Kompletní historie konverzací, její vyhledávání, procházení a opětovné otevření.
- Modelové function/tool calling, registr nástrojů a vykonávání volání podle rozhodnutí modelu.
- AI čtení souborů z povolených projektových složek.
- Bezpečné zápisy souborů, potvrzování uživatelem a automatické zálohy před změnou.
- Projektově oddělený kontext a paměť.
- Uživatelské rozhraní pro správu projektů.
- Přihlášení a řízení oprávnění pro více uživatelů.
- Ověřená GPU instalace a akcelerace.

## Další technické úkoly

1. Otestovat portable instalaci na čistém Windows.
2. Otestovat systémovou Python variantu Windows.
3. Otestovat Linuxový launcher na Debianu/Ubuntu včetně vytvoření `.venv`.
4. Ověřit instalaci a použití `llama-cpp-python` a embedding modelu.
5. Prověřit chování paměti při chybějícím modelu a při souběžných požadavcích.
6. Přidat automatické testy backendu a bezpečnostních omezení.
7. Teprve poté pokračovat v historii konverzací, projektovém kontextu a tool calling.
8. Historické soubory odstraňovat až po porovnání a archivaci.

## Poznámka k ověření

V této etapě byly upraveny texty spouštěcích skriptů a dokumentace na pracovní větvi. Nebyl spuštěn Windows batch soubor, Linuxový shell skript ani samotná aplikace. Nebyla ověřena instalace balíčků, funkčnost modelů ani runtime chování.
