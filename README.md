# MojeAI

MojeAI je lokální webová aplikace s jednoduchým chatovacím rozhraním. Slouží jako vlastní uživatelská a integrační vrstva nad cloudovými modely, lokálními GGUF modely a Ollamou. Není náhradou za Ollamu.

Projekt je ve vývoji. Aktuální zdrojový kód už je rozdělený do modulů, ale řada zamýšlených funkcí zatím není dokončená.

## Co současná verze obsahuje

- Chat s cloudovými poskytovateli Gemini, DeepSeek, OpenAI a Claude.
- Volitelné použití lokálních GGUF modelů přes `llama-cpp-python`.
- Rozpoznání dostupných modelů Ollamy, pokud běží její lokální API.
- Základní dlouhodobou paměť: textové záznamy a vyhledávání podle embeddingů v SQLite.
- Ruční povolení internetového vyhledávání; prefix `//` vynutí hledání.
- Nahrávání souborů PDF, TXT, MD, PY a CSV do konverzačního požadavku.
- Nastavení systémového promptu, výkonových parametrů a API klíčů.
- Základní evidenci projektů a jejich povolených složek přes API.

### Co zatím hotové není

- Ukládání a procházení kompletní historie konverzací.
- Skutečné předávání nástrojů modelu (function/tool calling) a automatické rozhodování modelu o jejich použití.
- Čtení a bezpečné úpravy souborů prostřednictvím AI; neexistuje potvrzovací workflow ani zálohování před zápisem.
- Oddělená paměť jednotlivých projektů a propojení projektů s chatem.
- Plnohodnotné uživatelské rozhraní pro správu projektů.
- Streaming odpovědí.

## Požadavky

- Python 3.12 je doporučená verze pro současné portable prostředí.
- Základní knihovny z `requirements.txt`.
- Pro lokální GGUF modely a sémantické vyhledávání v paměti také `llama-cpp-python`.
- Pro sémantickou paměť soubor embedding modelu `nomic-embed-text-v1.5.Q8_0.gguf` ve složce `modely/`.
- Pro použití Ollamy samostatně nainstalovaná a spuštěná Ollama.

## Spuštění

### Windows – doporučené portable prostředí

Portable instalace používá Embedded Python uložený v projektu. Otevři příkazový řádek v kořenové složce projektu a spusť:

```bat
setup_portable.bat
```

Skript stáhne Embedded Python 3.12.3, připraví pip a nainstaluje základní závislosti včetně CPU verze `llama-cpp-python`.

Potom spusť:

```bat
python\python.exe run.py
```

Při prvním použití paměti stáhni také embedding model:

```bat
python\python.exe stahni_model.py
```

Alternativně lze použít `run.py`, který spustí server portable Pythonem a otevře prohlížeč.

### Windows – systémový Python

Skript `spustit_cpu.bat` používá Python a pip dostupné v systému Windows. Není to portable režim. Nainstaluje pouze balíčky z `requirements.txt` a spustí `app.py`.

Pro lokální GGUF modely a sémantickou paměť je navíc nutné samostatně nainstalovat kompatibilní `llama-cpp-python` a stáhnout embedding model.

`spustit_gpu.bat` je historický instalační skript. Používá zastaralý seznam balíčků a automatická detekce grafické karty nezaručuje funkční GPU akceleraci. Pro běžné spuštění jej zatím nepoužívej.

### Linux

Z kořenové složky projektu:

```bash
chmod +x spustit.sh
./spustit.sh
```

Skript používá systémové `python3` a `pip3`, instaluje `requirements.txt` a spouští `app.py`. Neinstaluje `llama-cpp-python`; pro lokální GGUF modely a sémantickou paměť je proto nutné tuto závislost doplnit samostatně.

### Ruční spuštění

```bash
python -m pip install -r requirements.txt
python app.py
```

Aplikace naslouchá pouze na `127.0.0.1:5000`. Otevři:

```
http://localhost:5000
```

## API klíče

Klíč lze uložit přímo v postranním panelu aplikace. Aplikace jej ukládá do souboru `api_klic/<provider>.txt`.

Alternativně vytvoř soubor ručně, například:

```text
api_klic/gemini.txt
```

Do souboru vlož pouze samotný klíč. Stejný postup platí pro `deepseek.txt`, `openai.txt` a `claude.txt`.

Soubory `api_klic/*.txt` jsou ignorované Gitem. Soubory `*.txt.example` v repozitáři jsou pouze prázdné zástupné soubory, nikoli předvyplněné šablony.

Před commitem můžeš spustit:

```bash
python kontrola_klicu.py
```

Kontrola hledá známé formáty klíčů ve skutečných souborech `.txt`. Nenahrazuje kontrolu změn v Gitu a nezaručuje odhalení všech tajných údajů.

## Bezpečnostní upozornění

- Aplikace je určena pouze pro lokální použití. Nemá přihlašování a není připravena k vystavení do internetu ani do nedůvěryhodné sítě.
- Backend omezuje požadavky na lokální Host a kontroluje Origin u změnových požadavků. Tato omezení nejsou náhradou autentizace ani úplným bezpečnostním auditem.
- Do Gitu nikdy nevkládej skutečné API klíče, osobní konfiguraci, databáze, paměť ani stažené modely.
- Připojení složky v současné aplikaci pouze eviduje její cestu; samo o sobě neznamená, že AI umí její obsah číst nebo měnit.

## Důležité soubory

- `app.py` – vytvoření Flask aplikace a lokální bezpečnostní omezení.
- `config.py` – cesty a načítání konfigurace.
- `core/providers.py` – komunikace s poskytovateli modelů.
- `core/memory.py` – ukládání a vyhledávání dlouhodobé paměti.
- `core/projects.py` – evidence projektů a povolených složek.
- `routes/` – API endpointy.
- `static/` a `templates/` – webové rozhraní.
- `requirements.txt` – základní Python závislosti.
- `setup_portable.bat` – příprava portable Pythonu ve Windows.
- `run.py` – spuštění přes portable Python.
- `stahni_model.py` – stažení embedding modelu.

## Stav projektu a plán

Podrobnější přehled implementovaných částí a dalšího postupu je v [STATUS.md](STATUS.md) a [CHECKLIST.md](CHECKLIST.md). Inventura repozitáře je v [docs/REPOSITORY_AUDIT.md](docs/REPOSITORY_AUDIT.md).

## Licence

GPL-3.0 – viz [LICENSE](LICENSE).
