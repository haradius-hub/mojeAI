# MojeAI – projektový checklist

Checklist rozlišuje existující části kódu od funkcí, které jsou teprve plánované. Zaškrtnutí znamená, že odpovídající implementace je ve zdrojovém stromu; samo o sobě nepotvrzuje úspěšný runtime test.

## Aktuální základ

- [x] Modulární Flask aplikace (`app.py`, `config.py`, `core/`, `routes/`).
- [x] Webové chatovací rozhraní.
- [x] Cloudové providery Gemini, DeepSeek, OpenAI a Claude.
- [x] Detekce lokálních GGUF souborů a jejich obsluha přes `llama-cpp-python`.
- [x] Volitelné napojení na lokální API Ollamy.
- [x] SQLite databáze dlouhodobé paměti a textové záznamy v `pamet/`.
- [x] Sémantické vyhledávání paměti přes embedding model a `llama-cpp-python`.
- [x] Základní internetové vyhledávání a získání počasí.
- [x] Nahrávání PDF, TXT, MD, PY a CSV v rámci chatového požadavku.
- [x] Ukládání API klíčů do lokálních souborů.
- [x] Základní databázová evidence projektů a povolených složek přes API.
- [x] Omezení Flask serveru na lokální Host a kontrola Origin u změnových požadavků.
- [x] Portable instalační skript pro Embedded Python ve Windows.

## Provozní cesty

- [x] Portable Windows: `setup_portable.bat` + `python\python.exe run.py`.
- [x] Windows systémový Python: `spustit_cpu.bat`.
- [x] Linux systémový Python: `spustit.sh`.
- [ ] Sjednotit a ověřit instalační postupy pro všechny podporované platformy.
- [ ] Opravit nebo nahradit historický `spustit_gpu.bat`.
- [ ] Ověřit instalaci portable prostředí na čistém Windows.
- [ ] Ověřit instalaci a spuštění na podporované distribuci Linuxu.
- [ ] Připravit jasný postup instalace `llama-cpp-python` pro systémový Python.

## Funkce plánované – zatím nejsou hotové

- [ ] Historie konverzací: ukládání, seznam, vyhledávání a opětovné otevření.
- [ ] Projektové rozhraní v UI.
- [ ] Oddělení kontextu a paměti podle projektu.
- [ ] Skutečné tool/function calling podporované jednotlivými providery.
- [ ] Registr nástrojů a bezpečné vykonávání volání.
- [ ] Čtení souborů z výslovně povolených složek.
- [ ] Zápis a úpravy souborů až po potvrzení uživatelem.
- [ ] Automatická záloha před každou změnou souboru.
- [ ] Zobrazení průběhu a streaming odpovědí.
- [ ] Uživatelské přihlášení, pokud bude aplikace někdy dostupná mimo localhost.
- [ ] Více modelů v týmovém pracovním postupu.

## Údržba repozitáře

- [x] Záložní větev obnoveného projektu existuje.
- [x] Pracovní větev `cleanup/repository-audit` je oddělená od `main`.
- [x] Inventura repozitáře je v `docs/REPOSITORY_AUDIT.md`.
- [ ] Dokončit revizi dokumentace a ověřit odkazy na existující soubory.
- [ ] Prověřit Windows spouštěcí skripty a závislosti.
- [ ] Porovnat historické kopie před archivací nebo odstraněním.
- [ ] Přidat automatické testy.
- [ ] Zkontrolovat celý diff pracovní větve.
- [ ] Předložit změny ke schválení před případným sloučením do `main`.

## Testy

- [ ] Importní test aplikace v čistém prostředí.
- [ ] Test vytvoření Flask aplikace a základního endpointu.
- [ ] Test ukládání a načítání konfigurace.
- [ ] Test validace a ukládání API klíčů bez použití skutečných klíčů.
- [ ] Test paměti s dostupným i chybějícím embedding modelem.
- [ ] Test CRUD operací projektů a oprávnění složek.
- [ ] Test odmítnutí požadavků s nepovoleným Host/Origin.
- [ ] Test nahrávání povolených a nepovolených typů souborů.

## Pravidla další práce

1. Zachovat složku `python/`, protože je součástí Windows portable distribuce.
2. Změny připravovat na pracovní větvi, nikoli přímo na `main`.
3. Neodstraňovat historické soubory bez porovnání a bezpečné archivace.
4. Po každé etapě zkontrolovat změny a uvést, co bylo skutečně otestováno.
