# MojeAI – projektový checklist

Checklist rozlišuje existující implementaci od plánovaných funkcí. Zaškrtnutí znamená, že odpovídající kód je přítomen; samo o sobě nepotvrzuje úspěšný runtime test.

## Aktuální základ

- [x] Modulární Flask aplikace a webové chatovací rozhraní.
- [x] Cloudové providery Gemini, DeepSeek, OpenAI a Claude.
- [x] Detekce lokálních GGUF souborů a jejich obsluha přes `llama-cpp-python`.
- [x] Volitelné napojení na lokální API Ollamy.
- [x] SQLite databáze dlouhodobé paměti a textové záznamy.
- [x] Sémantické vyhledávání paměti přes embedding model a `llama-cpp-python`.
- [x] Základní internetové vyhledávání a získání počasí.
- [x] Nahrávání PDF, TXT, MD, PY a CSV v rámci chatového požadavku.
- [x] Ukládání API klíčů do lokálních souborů.
- [x] Základní databázová evidence projektů a povolených složek přes API.
- [x] Omezení Flask serveru na lokální Host a kontrola Origin u změnových požadavků.

## Spouštění a instalace – skripty upraveny, čekají na test

- [x] Windows nabídka `spustit.bat` rozlišuje portable a systémový Python.
- [x] Portable setup kontroluje chyby stažení a instalace základních závislostí.
- [x] Windows systémový launcher používá `python -m pip` a kontroluje výsledek instalace.
- [x] Zastaralá GPU varianta je vypnutá, aby nebyla nabízena jako funkční.
- [x] Linuxový launcher používá lokální virtuální prostředí `.venv`.
- [ ] Ověřit portable instalaci na čistém Windows.
- [ ] Ověřit systémový Python launcher na Windows.
- [ ] Ověřit Linuxový launcher na Debianu/Ubuntu.
- [ ] Ověřit instalaci `llama-cpp-python` a embedding modelu.
- [ ] Navrhnout a otestovat podporovaný GPU postup.

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
- [x] Dokumentace byla upravena podle aktuálního kódu.
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
