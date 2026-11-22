# Audit repozitáře a návrh úklidu

Datum kontroly: 22. 11. 2026  
Základ auditu: obnovený commit `fb8f12427bb5eeb60b471b6789788247718f6509`.

Tento dokument je inventura. Sám o sobě nic nemaže ani nepřesouvá. Úklid se má provést po jednotlivých dávkách a ověřit spuštěním aplikace.

## Zásadní rozhodnutí

- Složka `python/` zůstává v repozitáři. Je součástí Windows portable instalace a její odstranění by rozbilo očekávaný způsob spuštění.
- Zůstávají také `setup_portable.bat`, `get-pip.py` a `run.py`, protože spolu tvoří část instalačního/spouštěcího řetězce.
- Veškeré úpravy se nejprve provádějí na větvi `cleanup/repository-audit`. `main` zůstává nedotčená.
- Zatím se nemění závislosti ani spouštěcí skripty. Některé vypadají zastarale, ale jejich skutečné chování musí být ověřeno na Windows.

## 1. Zachovat

### Jádro aplikace
- `app.py`
- `config.py`
- `core/__init__.py`
- `core/memory.py`
- `core/projects.py`
- `core/providers.py`
- `routes/__init__.py`
- `routes/chat.py`
- `routes/config.py`
- `routes/memory.py`
- `routes/projects.py`
- `static/app.js`
- `static/style.css`
- `templates/index.html`

Důvod: jde o aktuálně používanou modulární aplikaci a její UI/API.

### Windows portable provoz
- `python/` – ponechat celý adresář beze změn; je součástí současné Windows portable instalace.
- `setup_portable.bat` – připravuje Embedded Python a instaluje závislosti.
- `get-pip.py` – instalační skript jej používá, pokud chybí.
- `run.py` – spouští aplikaci přes `python/python.exe`.
- `spustit.bat`, `spustit_cpu.bat`, `spustit_gpu.bat` – zachovat do ověření jejich aktuální funkčnosti; hlavní nabídka na ně odkazuje.
- `stahni_model.py` – stahuje embedding model, na který odkazuje launcher a checklist.
- `requirements.txt` – aktuální základní seznam závislostí; zatím neupravovat.
- `api_klic/*.txt.example` a `api_klic/README.md` – šablony a instrukce pro API klíče.
- `www/README.md` – vysvětluje umístění volitelných portable prohlížečů; samotné prohlížeče zůstávají mimo Git.

### Ostatní
- `LICENSE`
- `.gitignore`
- `.gitattributes`
- `favicon.ico`
- `klavesove_zkratky.txt` – ponechat; obsahuje uživatelské pokyny, nikoli zjevný technický odpad.

## 2. Přesunout nebo ponechat mimo hlavní zdrojový strom

Tato skupina není pokyn k odstranění dat uživatele. Jde o soubory, které se lépe hodí do dokumentace, archivu nebo distribučního balíčku.

- `python/`: nyní ponechat přímo v repozitáři podle výslovného rozhodnutí. Do budoucna lze zvážit samostatný release ZIP, ale až bude existovat ověřený instalační postup, který portable Python spolehlivě stáhne nebo získá z release.
- `www/*/`: portable prohlížeče mají být mimo Git; současný `.gitignore` už je ignoruje. Ponechat pouze `www/README.md`.
- `get-pip.py`: nyní ponechat, protože jej používá `setup_portable.bat`. Případné stažení při instalaci místo verzování lze řešit později.
- Historické zálohy kódu s příponami `.old`, `.old1`, `.backup`, `-OLD`, `-OLD1` apod.: před odstraněním porovnat s aktuální verzí a případně přesunout do samostatného archivu mimo aktivní strom. Nejsou importovány běžnou aplikací, ale mohou obsahovat užitečný historický kód.

## 3. Kandidáti na odstranění z aktivního repozitáře

Odstranění doporučuji až po vytvoření archivní kopie a kontrole, že na soubory nic neodkazuje.

| Soubor | Důvod | Doporučený postup |
|---|---|---|
| `config.py-OLD` | stará kopie aktivního `config.py` | archivovat, poté odstranit |
| `gitignore` | duplicitní starší varianta; skutečný soubor je `.gitignore` | odstranit po porovnání |
| `jak spustit.txt` | obsahuje jen URL aplikace | odstranit; informaci doplnit do README |
| `📂 Výsledná struktura.txt` | historický popis starší struktury | odstranit po převzetí případně užitečných poznámek |
| `📂 Výsledná struktura2.txt` | další historický popis struktury | odstranit po převzetí případně užitečných poznámek |
| `requirements_cpu.txt` | starší seznam závislostí včetně ChromaDB/Torch; aktuální kód používá jinou lehčí sadu | odstranit po ověření, že jej žádný podporovaný postup nepoužívá |
| `requirements-cpu.txt` | starý instalační profil s PyTorch a starší verzí llama-cpp-python | prověřit, archivovat a následně odstranit, pokud není podporován |
| `requirements-cuda.txt` | starý CUDA profil s PyTorch | prověřit, archivovat a následně odstranit, pokud není podporován |
| `core/providers.py.old`, `core/providers.py.old1` | staré kopie aktivního modulu | archivovat nebo odstranit |
| `routes/chat.py.backup` | záloha aktivního modulu | archivovat nebo odstranit |
| `static/app.js-OLD`, `static/app.js-OLD1` | staré kopie frontendového skriptu | archivovat nebo odstranit |
| `templates/index.html-OLD`, `index.html-OLD1`, `index.html-OLD2`, `index.html-OLD3` | staré kopie šablony | archivovat nebo odstranit |

### Zvláštní případ: poškozená dokumentace

Tyto soubory nejsou vhodné k prostému odstranění. Je potřeba je nahradit čistým obsahem:

- `README.md` – obsahuje starý popis prototypu a omylem vložené bloky `<BDS:create_file>` včetně textů dalších souborů.
- `api_klic/README.md` – stejným způsobem obsahuje slepené obsahy šablon a části skriptu; musí se přepsat na čistý návod.
- `STATUS.md` – stav k 1. 11. 2026, obsahuje neověřené nebo zastaralé údaje a staré osobní detaily o modelu/hardwaru.
- `CHECKLIST.md` – stav k 31. 10. 2026, některé položky si odporují se současným kódem.

Odkazované soubory `GIT_SETUP.md`, `kontrola_klicu.py` a `config.example.json` v aktuálním stromu nejsou. Dokumentace na ně proto nesmí odkazovat jako na existující součásti, dokud nebudou skutečně vytvořeny.

## Důležitá technická upozornění před úklidem

1. `spustit_cpu.bat` používá systémový Python a `requirements.txt`, zatímco `run.py` používá Embedded Python ve složce `python/`. README musí jasně rozlišovat tyto režimy.
2. `spustit_gpu.bat` instaluje staré balíčky včetně ChromaDB, Torch a Transformers. To je v rozporu s aktuálním lehkým `requirements.txt`; před jeho označením za podporovaný GPU launcher je nutné jej opravit a otestovat.
3. `spustit_en.bat` je další historická varianta, která používá systémový Python a spouští server jiným způsobem. Zatím ji nemažeme, ale je kandidátem na pozdější sjednocení nebo odstranění.
4. `spustit.sh` používá systémový Linux Python. Je to samostatná cesta, nikoli Windows portable launcher.
5. `requirements.txt` obsahuje `flask-cors`, přestože aktuální `app.py` CORS middleware nepoužívá. Zatím neodebírat bez ověření importů a závislostí.
6. V repozitáři zatím není adresář `tests/`. Před sloučením úklidu je potřeba alespoň ověřit import aplikace, inicializaci SQLite projektů a základní API endpointy.

## Navržené pořadí práce

1. Opravit README a `api_klic/README.md`; aktualizovat STATUS a CHECKLIST podle skutečného kódu.
2. Prověřit a sjednotit spouštěcí cesty Windows CPU/GPU/portable.
3. Archivovat a odstranit potvrzené historické kopie a duplicitní soubory.
4. Přidat minimální automatické testy a provést instalační/spouštěcí kontrolu.
5. Zkontrolovat diff celé větve a teprve potom otevřít Pull Request do `main`.

Žádný krok tohoto auditu neznamená odstranění složky `python/`. Ta zůstává zachována.
