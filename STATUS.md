# MojeAI – aktuální stav projektu

Tento dokument popisuje stav zjištěný kontrolou zdrojového kódu a dosavadním praktickým ověřením v pracovní větvi `cleanup/repository-audit`. Uživatel potvrdil funkční spuštění Windows portable varianty a funkční výběr i připojení složky v aplikaci. Systémový Python na Windows a Linux zatím prakticky ověřeny nebyly.

## Vize

MojeAI má být přenositelná aplikační a orchestrace vrstva pro různé modely – cloudové i lokální. Ollama zůstává samostatným backendem, nikoli konkurentem, kterého by projekt měl znovu implementovat.

Dlouhodobým cílem je osobní AI pracovní prostředí s historií, dlouhodobou a projektovou pamětí, skutečným tool calling a bezpečnou prací se soubory. Současný kód představuje pouze základ této vize.

## Implementované části

### Aplikace a modely
- Modulární Flask aplikace: `app.py`, `config.py`, `core/`, `routes/`, `static/` a `templates/`.
- Chatovací rozhraní a nastavení systémového promptu, modelu, API klíčů, internetu a parametrů lokálního modelu.
- Poskytovatelé Gemini, DeepSeek, OpenAI a Claude. Gemini používá `google-genai` a Interactions API s modelem `gemini-3.8-flash`; požadavky jsou nastaveny jako `store=False`, aby se konverzace neukládala do serverové historie Gemini.
- Lokální GGUF modely přes `llama-cpp-python`.
- Připojení k lokálnímu API Ollamy a načtení seznamu modelů.
- Základní internetové vyhledávání a získání počasí.
- Přijetí PDF, TXT, MD, PY, CSV, HTM/HTML, CSS, JS, DOCX, XLSX, PPTX, ODT, ODS a ODP do konkrétního chatového požadavku. CSV zůstává podporováno; nové kancelářské formáty se extrahují do textového kontextu.
- Výběr souboru zobrazuje před odesláním kartu s názvem, typem a velikostí; přílohu lze odebrat. Uživatelská zpráva po odeslání zobrazuje název přílohy. Jde o přehled přílohy, nikoli o náhled obsahu dokumentu.
- Výběr složky systémovým dialogem a její přidání do seznamu připojených složek; uživatel potvrdil funkčnost v Windows portable variantě.

### Paměť a projekty
- Dlouhodobá paměť používá SQLite databázi `data/pamet.db` a textové záznamy ve složce `pamet/`.
- Sémantické vyhledávání vyžaduje `llama-cpp-python` a model `nomic-embed-text-v1.5.Q8_0.gguf`.
- Backend eviduje projekty, popisy, instrukce a povolené složky v hlavní databázi `data/mojeai.db`. Historická `data/projects.db` se při prvním startu importuje read-only migrací a zůstává zachována. Projekty zatím nejsou propojené s chatem ani oddělenou pamětí.

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

## Gemini API

- Staré `google-generativeai` a model `gemini-2.0-flash` byly nahrazeny SDK `google-genai` a Interactions API s `gemini-3.8-flash`.
- Gemini volání používá `store=False`; kontext aplikace se předává jako jeden textový vstup a serverová historie Interactions se neukládá.
- Kód byl staticky zkontrolován, skutečný API požadavek s uživatelským klíčem zatím nebyl proveden.

## Databázový základ – první implementační etapa

- Hlavní SQLite databáze `data/mojeai.db` je inicializována verzovaným migračním mechanismem.
- Migrace 1 vytváří tabulky projektů, povolených složek a index.
- Migrace 2 bezpečně kopíruje existující projekty a složky z `data/projects.db`, zachovává jejich ID a původní databázi otevírá pouze pro čtení.
- Migrace jsou evidovány v tabulce `schema_migrations`; každá změna schématu/import je provedena v transakci.
- `data/pamet.db` a soubory ve složce `pamet/` zůstávají mimo tuto migraci a nejsou upravovány.
- Přidány automatické testy migrace: čistá databáze, zachování dat, opakované spuštění, odmítnutí vadného schématu a CRUD projektů.
- Migrace 3 vytváří tabulky `conversations`, `messages` a `attachments` včetně indexů a omezení rodičovské zprávy na stejnou konverzaci.
- Tabulka `attachments` eviduje více příloh u jedné zprávy (název, úložnou cestu, MIME typ, velikost, SHA-256 a čas); binární ukládání souborů ani upload API zatím nejsou implementovány.
- Testy migrací 1–3 a vztahů historie byly doplněny, ale nové testy migrace 3 zatím nebyly spuštěny v runtime.

## Co není implementováno

- Uživatelské UI pro seznam, vyhledávání, procházení a opětovné otevření historie konverzací. Základní ukládání zpráv přes API a návaznost v právě otevřené stránce už jsou implementovány.
- Modelové function/tool calling, registr nástrojů a vykonávání volání podle rozhodnutí modelu.
- AI čtení souborů z povolených projektových složek.
- Bezpečné zápisy souborů, potvrzování uživatelem a automatické zálohy před změnou.
- Projektově oddělený kontext a paměť.
- Uživatelské rozhraní pro správu projektů.
- Přihlášení a řízení oprávnění pro více uživatelů.
- Ověřená GPU instalace a akcelerace.
- Rozšířené zpracování dokumentů DOCX, XLSX, PPTX, ODT, ODS a ODP.
- Nahrávání obrázků PNG, JPG/JPEG a WebP a jejich předávání multimodálním modelům.

## Stav rozšíření práce se soubory

- UI přehled jedné vybrané přílohy je implementován. Skutečné obrazové náhledy a multimodální zpracování obrázků zatím hotové nejsou.

- Kód pro extrakci DOCX, XLSX, PPTX, ODT, ODS a ODP je přidán do `core/file_processing.py`.
- Chatový endpoint a výběr souboru v UI přijímají DOCX, XLSX, PPTX, ODT, ODS a ODP; CSV zůstává podporováno.
- Chatový endpoint a výběr souboru v UI nově přijímají také `.htm`, `.html`, `.css` a `.js`. Tyto soubory se předávají modelu jako zdrojový text; JavaScript se nespouští. Runtime test HTML přílohy je připraven, ale zatím nebyl spuštěn.
- Závislosti `python-docx`, `openpyxl`, `python-pptx` a `odfpy` jsou v `requirements.txt`; portable setup kontroluje jejich přítomnost.
- Extrakce dokumentů převádí text a dostupné tabulkové hodnoty na textový kontext. Nejde o zachování původního formátování ani o obrazovou analýzu vložených obrázků.
- Je zavedena kontrola ZIP kontejnerů a limit 100 000 znaků extrahovaného textu.
- Implementace zatím čeká na runtime testy skutečnými dokumenty a na ověření všech tří instalačních cest.

### Další práce se soubory

1. Přidat nahrávání obrázků PNG, JPG/JPEG a WebP a jejich předávání providerům/modelům s podporou obrazového vstupu.
2. Otestovat PDF, TXT, MD, PY, CSV, DOCX, XLSX, PPTX, ODT, ODS a ODP; ověřit extrakci textu/tabulek, chybné a poškozené soubory, nepodporované typy a limity velikosti.
3. Otestovat Windows portable instalaci po doplnění nových závislostí, systémový Python a Linux.

## Další technické úkoly

1. Otestovat portable instalaci na čistém Windows.
2. Otestovat systémovou Python variantu Windows.
3. Otestovat Linuxový launcher na Debianu/Ubuntu včetně vytvoření `.venv`.
4. Ověřit instalaci a použití `llama-cpp-python` a embedding modelu.
5. Prověřit chování paměti při chybějícím modelu a při souběžných požadavcích.
6. Přidat automatické testy backendu a bezpečnostních omezení.
7. Dokončit runtime ověření historie API a následně přidat UI pro seznam a opětovné otevření konverzací.
8. Navázat bezpečnou správou projektových souborů a izolovaným náhledem HTML kalkulaček.
8. Historické soubory odstraňovat až po porovnání a archivaci.

## Poznámka k ověření

Windows portable aplikaci a připojování složek prakticky ověřil uživatel. Asistent neprováděl samostatný runtime test. Systémový Python, Linuxový launcher, GPU, embedding model a rozšířené formáty souborů zůstávají neověřené.

## Historie konverzací – druhá implementační etapa

- Přidán `core/conversations.py` s oddělenou servisní vrstvou pro vytvoření, výpis, načítání a doplňování konverzací a zpráv.
- Výpis konverzací podporuje stránkování a počet zpráv; načtení konverzace vrací zprávy i metadata připojených souborů.
- Validují se role, délky vstupů, stavy zpráv, stránkovací parametry a rodičovské vazby. SQL dotazy používají parametry.
- `routes/chat.py` nyní ukládá uživatelskou zprávu před voláním modelu a odpověď jako navazující zprávu. Při dalším požadavku se uživatelská zpráva naváže na předchozí odpověď.
- Chatové UI předává a uchovává ID právě aktivní konverzace během otevřené stránky. Po obnovení stránky se zatím automaticky nenačte seznam historie; uživatelské procházení a znovuotevření chatů ještě není implementováno.
- Při výjimce modelu nebo chybové odpovědi poskytovatele se uloží uživatelský dotaz i neúspěšná odpověď se stavem `failed`.
- Dlouhodobá paměť `pamet.db` zůstává zachována a nadále se používá odděleně od historie.
- Binární přílohy a jejich metadata se zatím trvale neukládají do historie; upload pipeline zůstává samostatnou etapou.
- Přidány API testy v `tests/test_chat_api.py`; čekají na runtime spuštění spolu se stávajícími testy.
