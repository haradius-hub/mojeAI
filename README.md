# MojeAI

MojeAI je lokální webová aplikace pro chat s cloudovými i lokálními jazykovými modely. Poskytuje vlastní uživatelské rozhraní a základní dlouhodobou paměť. Ollamu nenahrazuje – umí se k ní připojit jako ke službě.

Projekt je ve vývoji. Níže je popsáno, co současná verze skutečně nabízí a jak ji spustit.

## Rychlé spuštění

### Windows – doporučená portable varianta

1. Stáhni nebo rozbal projekt.
2. Spusť `spustit.bat`.
3. Vyber možnost **1 – Portable Python**.
4. Po dokončení instalace se spustí aplikace a otevře prohlížeč.

Portable instalace stáhne Embedded Python 3.12.3 a připraví prostředí přímo ve složce projektu. Nainstaluje základní knihovny a pokusí se přidat také CPU verzi `llama-cpp-python`. Pokud se tato doplňková instalace nepodaří, cloudové modely mohou fungovat dál, ale lokální GGUF modely a sémantická paměť nebudou dostupné.

Případně lze kroky provést ručně:

```bat
setup_portable.bat
python\python.exe run.py
```

Pro sémantickou paměť je potřeba ještě stáhnout embedding model:

```bat
python\python.exe stahni_model.py
```

### Windows – systémový Python

Pokud už máš Python nainstalovaný ve Windows, spusť `spustit.bat` a vyber možnost **2 – Systémový Python (CPU)**.

Tato varianta nainstaluje balíčky z `requirements.txt` do zvoleného systémového Pythonu. Pro lokální GGUF modely a sémantickou paměť je navíc nutné samostatně nainstalovat kompatibilní `llama-cpp-python` a stáhnout embedding model.

### Linux – Debian, Ubuntu a odvozené distribuce

V terminálu přejdi do složky projektu a spusť:

```bash
chmod +x spustit.sh
./spustit.sh
```

Skript vytvoří lokální virtuální prostředí `.venv`, nainstaluje do něj `requirements.txt` a spustí aplikaci. Na Debianu/Ubuntu může být nejprve potřeba doinstalovat:

```bash
sudo apt install python3-venv
```

Linuxový instalační skript zatím nepřidává `llama-cpp-python`. Bez něj fungují cloudové poskytovatele, ale ne lokální GGUF modely ani sémantická paměť.

Aplikace se otevře na adrese:

```
http://localhost:5000
```

Server naslouchá pouze na lokálním rozhraní.

## Co aplikace umí

- Chatovat přes API poskytovatelů Gemini, DeepSeek, OpenAI a Claude.
- Používat lokální GGUF modely přes `llama-cpp-python`.
- Připojit se k lokálně běžící Ollamě a zobrazit její dostupné modely.
- Ukládat textové záznamy dlouhodobé paměti do souborů a SQLite.
- Vyhledávat v paměti pomocí embeddingů; vyžaduje `llama-cpp-python` a embedding model.
- Vyhledávat na internetu a získávat počasí.
- Přijmout soubory PDF, TXT, MD, PY a CSV jako součást chatového požadavku.
- Ukládat API klíče do lokálních souborů.
- Evidovat projekty a povolené složky přes základní API.

## Co zatím aplikace neumí

Následující funkce jsou plánované, nikoli dokončené:

- Kompletní historii konverzací včetně procházení, vyhledávání a opětovného otevření chatů.
- Skutečné tool/function calling, při kterém model sám vybere nástroj a aplikace jej bezpečně vykoná.
- Číst obsah připojených projektových složek a pracovat s jejich soubory.
- Bezpečně zapisovat a upravovat soubory s potvrzením uživatele a zálohou.
- Oddělenou paměť a kontext pro jednotlivé projekty.
- Uživatelské rozhraní pro správu projektů.
- Ověřený GPU instalační a spouštěcí režim.

## API klíče

Klíče lze vložit přímo v postranním panelu aplikace. Ukládají se do souborů v adresáři `api_klic/`:

- `gemini.txt`
- `deepseek.txt`
- `openai.txt`
- `claude.txt`

Do souboru patří pouze samotný klíč. Soubory `api_klic/*.txt` jsou ignorované Gitem. Podrobnosti a odkazy na poskytovatele jsou v [api_klic/README.md](api_klic/README.md).

Nikdy necommituj skutečné klíče. Pokud se klíč dostane do veřejného repozitáře, zneplatni jej u poskytovatele a vytvoř nový.

## Bezpečnost a omezení

- Aplikace nemá přihlašování a je určena pouze pro lokální použití.
- Nevystavuj ji do internetu ani do nedůvěryhodné sítě.
- Kontrola lokálního Host a Origin není náhradou autentizace ani úplným bezpečnostním auditem.
- Do Gitu nepatří API klíče, osobní konfigurace, databáze paměti ani stažené modely.
- Evidence povolené složky zatím neznamená, že model umí její obsah číst nebo měnit.

## Struktura projektu

- `app.py`, `config.py` – spuštění aplikace a konfigurace.
- `core/` – poskytovatelé modelů, paměť a projekty.
- `routes/` – API endpointy.
- `static/`, `templates/` – webové rozhraní.
- `requirements.txt` – základní Python závislosti.
- `setup_portable.bat`, `run.py` – portable režim Windows.
- `spustit.bat`, `spustit_cpu.bat` – nabídka spuštění a systémový Python ve Windows.
- `spustit.sh` – Linuxový launcher s virtuálním prostředím.
- `stahni_model.py` – stažení embedding modelu.

Portable prohlížeče lze umístit do podsložek `www/`; jejich použití je volitelné. Viz [www/README.md](www/README.md).

## Stav a další vývoj

Aktuální stav implementace a plán práce jsou v [STATUS.md](STATUS.md) a [CHECKLIST.md](CHECKLIST.md). Technická inventura repozitáře je v [docs/REPOSITORY_AUDIT.md](docs/REPOSITORY_AUDIT.md).

## Licence

GPL-3.0 – viz [LICENSE](LICENSE).
