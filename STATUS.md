# MojeAI – aktuální stav projektu

Tento dokument popisuje stav zjištěný kontrolou zdrojového kódu a dosavadním praktickým ověřením v pracovní větvi `cleanup/repository-audit`. Uživatel potvrdil funkční spuštění Windows portable varianty a funkční výběr i připojení složky v aplikaci. Systémový Python na Windows a Linux zatím prakticky ověřeny nebyly.

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
- Přijetí PDF, TXT, MD, PY a CSV do konkrétního chatového požadavku. CSV je již součástí současné implementace.
- Výběr složky systémovým dialogem a její přidání do seznamu připojených složek; uživatel potvrdil funkčnost v Windows portable variantě.

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

### Prakticky ověřeno uživatelem

- Windows portable varianta se po instalaci/spuštění otevřela a aplikace fungovala.
- Systémový dialog pro výběr složky se otevře, vybraná složka se přidá a zobrazí v levém seznamu připojených složek.

Toto ověření se vztahuje na konkrétní uživatelské prostředí a testovanou verzi pracovní větve. Nejde o čistou instalaci na jiném počítači ani o ověření všech spouštěcích variant.

## Co není implementováno

- Kompletní historie konverzací, její vyhledávání, procházení a opětovné otevření.
- Modelové function/tool calling, registr nástrojů a vykonávání volání podle rozhodnutí modelu.
- AI čtení souborů z povolených projektových složek.
- Bezpečné zápisy souborů, potvrzování uživatelem a automatické zálohy před změnou.
- Projektově oddělený kontext a paměť.
- Uživatelské rozhraní pro správu projektů.
- Přihlášení a řízení oprávnění pro více uživatelů.
- Ověřená GPU instalace a akcelerace.
- Rozšířené zpracování dokumentů DOCX, XLSX, PPTX, ODT, ODS a ODP.
- Nahrávání obrázků PNG, JPG/JPEG a WebP a jejich předávání multimodálním modelům.

## Další etapa práce se soubory

1. Rozšířit zpracování dokumentů o DOCX, XLSX, PPTX, ODT, ODS a ODP; zachovat již existující podporu CSV.
2. Přidat nahrávání obrázků PNG, JPG/JPEG a WebP a navrhnout jejich předávání pouze providerům/modelům s podporou obrazového vstupu.
3. Otestovat všechny podporované formáty: extrakci textu a tabulek, obrázkové vstupy, chybné a poškozené soubory, nepodporované typy a limity velikosti.

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

Windows portable aplikaci a připojování složek prakticky ověřil uživatel. Asistent neprováděl samostatný runtime test. Systémový Python, Linuxový launcher, GPU, embedding model a rozšířené formáty souborů zůstávají neověřené.
