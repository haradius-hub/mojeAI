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

## Spouštění a instalace – částečně ověřeno

- [x] Windows nabídka `spustit.bat` rozlišuje portable a systémový Python.
- [x] Portable setup kontroluje chyby stažení a instalace základních závislostí.
- [x] Windows systémový launcher používá `python -m pip` a kontroluje výsledek instalace.
- [x] Zastaralá GPU varianta je vypnutá, aby nebyla nabízena jako funkční.
- [x] Linuxový launcher používá lokální virtuální prostředí `.venv`.
- [x] Uživatelsky ověřit spuštění Windows portable varianty a otevření aplikace.
- [x] Uživatelsky ověřit systémový výběr složky, její přidání a zobrazení v seznamu.
- [ ] Ověřit portable instalaci na čistém Windows / jiném počítači.
- [ ] Ověřit systémový Python launcher na Windows.
- [ ] Ověřit Linuxový launcher na Debianu/Ubuntu.
- [ ] Ověřit instalaci `llama-cpp-python` a embedding modelu.
- [ ] Navrhnout a otestovat podporovaný GPU postup.

## Rozšíření práce se soubory – implementováno, čeká na runtime test

Současné nahrávání v chatovém požadavku podporuje PDF, TXT, MD, PY a CSV. CSV zůstává zachováno.

- [x] Přidat extrakci obsahu z DOCX.
- [x] Přidat zpracování XLSX včetně listů a tabulkových hodnot.
- [x] Přidat zpracování PPTX včetně textu snímků a tabulek.
- [x] Přidat zpracování ODT, ODS a ODP.
- [x] Přidat nové formáty do výběru souboru v uživatelském rozhraní.
- [x] Přidat potřebné knihovny do `requirements.txt`.
- [x] Rozšířit kontrolu závislostí ve Windows portable setupu.
- [x] Omezit velikost extrahovaného textu a kontrolovat ZIP kontejner kancelářských dokumentů.
- [ ] Prakticky otestovat každý formát na reálném souboru.
- [ ] Otestovat poškozené dokumenty, nepodporované typy a překročení limitů.
- [ ] Ověřit novou portable instalaci a doplnění závislostí ve stávající portable instalaci.
- [ ] Ověřit systémový Python na Windows a Linuxový launcher.

Další pořadí: (1) obrázky PNG, JPG/JPEG a WebP včetně předávání multimodálním providerům, (2) společné testování všech podporovaných formátů. Kancelářské dokumenty se převádějí na textový kontext; vložené obrázky se zatím neanalyzují.

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

### Git a hostingové služby – plánované rozšíření

Cílem je umožnit MojeAI orientovat se v repozitářích a později v nich bezpečně pracovat. Integrace nemá být omezena pouze na GitHub; aplikace má používat jednotné rozhraní a konkrétní služby obsluhovat přes adaptéry.

- [ ] Navrhnout obecný systém integrací, připojení a oprávnění.
- [ ] Zavést jednotné rozhraní pro Git operace, nezávislé na konkrétním poskytovateli.
- [ ] GitHub – nejprve režim pouze pro čtení: repozitáře, soubory, větve, historie, commity, diff, issues, pull requesty a vyhledávání kódu.
- [ ] Gitea a Forgejo – podpora přes samostatné adaptéry, přednostně režim pouze pro čtení.
- [ ] Lokální Git – práce s lokálními repozitáři, stav pracovního stromu, diff, historie a větve.
- [ ] GitLab a další kompatibilní služby – rozšíření po ověření společného rozhraní.
- [ ] Obecné Git remote adresy přes HTTPS/SSH tam, kde je lze bezpečně obsloužit.
- [ ] Aktivní operace: vytvoření pracovní větve, příprava změn souborů, commit, push a vytvoření pull/merge requestu.
- [ ] Před každou operací měnící repozitář vyžadovat výslovné potvrzení uživatele; merge nepovolovat automaticky.
- [ ] Zobrazit návrh změn a diff před potvrzením zápisu nebo commitu.
- [ ] Ukládat přístupové tokeny a klíče odděleně od projektové paměti a nikdy je neposílat modelu jako běžný kontext.
- [ ] Považovat obsah repozitáře, README, issues i komentáře za nedůvěryhodná data, nikoli za instrukce, které mohou přepsat systémová pravidla nebo vyvolat neodsouhlasené akce.
- [ ] Omezovat oprávnění podle připojení a projektu; výchozí režim má být pouze pro čtení.

Doporučené pořadí: (1) obecný systém integrací a oprávnění, (2) GitHub read-only, (3) Gitea/Forgejo read-only, (4) lokální Git a pracovní větve, (5) schvalované zápisové operace, (6) GitLab a další poskytovatelé.

Tato část je plánem, nikoli potvrzením implementace. Jednotlivé integrace ani Git operace zatím nejsou tímto zápisem vytvořeny.

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
- [ ] Test extrakce obsahu DOCX, XLSX, PPTX, ODT, ODS a ODP.
- [ ] Test předávání PNG, JPG/JPEG a WebP multimodálním modelům.

## Pravidla další práce

1. Zachovat složku `python/`, protože je součástí Windows portable distribuce.
2. Změny připravovat na pracovní větvi, nikoli přímo na `main`.
3. Neodstraňovat historické soubory bez porovnání a bezpečné archivace.
4. Po každé etapě zkontrolovat změny a uvést, co bylo skutečně otestováno.
