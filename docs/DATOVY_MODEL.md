# Návrh společného datového modelu mojeAI

**Stav:** návrh po statickém auditu, zatím neimplementováno  
**Větev:** `cleanup/repository-audit`  
**Účel:** vytvořit společný a bezpečný datový základ pro historii, projekty a schválená rozšíření A–E.

Tento dokument popisuje cílový návrh. Neznamená, že jsou níže uvedené tabulky, API nebo migrace již vytvořené.

## 1. Shrnutí auditu současného stavu

Kontrola zdrojového kódu ve větvi `cleanup/repository-audit`:

| Oblast | Současný stav |
|---|---|
| Projekty | `data/projects.db`; tabulky `projects`, `project_folders`; základní CRUD a kontrola cest. |
| Dlouhodobá paměť | `data/pamet.db`; tabulka `pamet` s textem, zdrojem, časem a embeddingem. |
| Soubory paměti | Textové soubory ve složce `pamet/`; používají se také při výpisu posledních záznamů. |
| Konverzace | Není nalezeno trvalé ukládání konverzací ani jednotlivých zpráv. |
| Frontend chatu | Zprávy se přidávají do aktuálního DOM; po obnovení stránky není k dispozici historie k opětovnému načtení. |
| Vazba projektu na chat | V chatovém API není předáváno ani ukládáno `project_id`. |
| Projektové zdroje | Povolené složky se evidují, ale současný chat je neumí používat jako skutečné nástroje pro čtení/zápis. |
| Úlohy a schvalování | Neexistuje persistentní evidence úloh, událostí úloh ani žádostí o schválení. |
| Databázové migrace | V prohlédnutých modulech nebyl nalezen verzovaný migrační mechanismus. Tabulky se vytvářejí pomocí `CREATE TABLE IF NOT EXISTS`. |

### Důležitý rozdíl: historie není paměť

Současná chatová routa ukládá otázku a odpověď do sémantické paměti přes `memory_manager.uloz()`. Při internetovém vyhledávání ukládá také jeho dotaz a výsledek.

To není plnohodnotná historie:
- chybí identita konverzace a zprávy;
- nelze bezpečně obnovit přesné pořadí a návaznost zpráv;
- není možné vyhledat a znovu otevřít konkrétní chat jako celek;
- není možné větvit konverzaci;
- běžné chatové záznamy se míchají s dlouhodobou sémantickou pamětí.

Toto chování se musí změnit až v samostatné migrační etapě. Stávající záznamy paměti se nesmějí automaticky mazat.

## 2. Doporučená strategie databází

Nedoporučuji vytvářet samostatnou databázi pro každou novou funkci. Vztahy mezi projekty, chaty, poznámkami, úlohami a schvalováním jsou důležité a mají být spravovány transakčně.

### Navržené rozdělení

1. **`data/mojeai.db` – hlavní relační databáze aplikace**
   - projekty a povolené složky;
   - konverzace, větve a zprávy;
   - metadata příloh a projektových zdrojů;
   - pracovní poznámky a jejich verze;
   - profily AI a jejich verze;
   - definice nástrojů a oprávnění;
   - žádosti o schválení;
   - úlohy, události úloh a auditní události;
   - verze databázového schématu.

2. **`data/pamet.db` – stávající sémantická paměť**
   - prozatím zachovat její specializované ukládání embeddingů;
   - oddělit její obsah od historie konverzací;
   - později rozhodnout, zda ji ponechat samostatně, nebo bezpečně převést do hlavní databáze;
   - žádná automatická hromadná konverze ani mazání starých záznamů.

3. **`config.json`, adresář `api_klic/` a soubory modelů**
   - zůstávají oddělené od relačních dat;
   - tajné klíče se nikdy neukládají do historie, poznámek, profilů ani auditních výpisů.

Současnou `projects.db` je možné při migraci převést do `mojeai.db`. Původní databáze musí zůstat jako záloha, dokud nebude migrace ověřena na kopii i na skutečných datech. Starou databázi nemažeme v rámci první migrace.

## 3. Základní relační entity

Všechny nové entity mají používat stabilní textová ID (UUID), nikoli ID závislá na pořadí záznamů. Časy ukládat v UTC v jednotném ISO 8601 formátu.

### 3.1 Projekty a oprávnění

**projects**
- `id`, `name`, `description`, `instructions`
- `created_at`, `updated_at`, případně `archived_at`

**project_folders**
- `id`, `project_id`, `path`, `access`, `added_at`
- `access` zůstává omezeno na `read` a `read_write`.

Stávající projektová data se zachovají. Projektová oprávnění se budou ověřovat na serveru při každém použití zdroje nebo nástroje.

### 3.2 Konverzace, větve a zprávy

**conversations**
- `id`, `project_id` (NULL znamená osobní/globální prostor)
- `title`, `created_at`, `updated_at`, `archived_at`

**conversation_branches**
- `id`, `conversation_id`, `name`
- `forked_from_message_id` (NULL pro výchozí větev)
- `created_at`, `created_by`, `is_default`

**messages**
- `id`, `conversation_id`, `branch_id`
- `parent_message_id` (NULL pouze pro kořen zpráv dané návaznosti)
- `role` (system/user/assistant/tool podle podporovaného API)
- `content`, `created_at`
- `provider`, `model`, `profile_version_id` jako metadata odpovědi
- volitelně `status`, `error_code`, `duration_ms`, `usage_json`

Zprávy se při vytvoření větve nemají kopírovat. Nová větev odkazuje na zprávu, ze které odbočila, a ukládá pouze vlastní pokračování. Při sestavování kontextu aplikace projde rodičovské vazby a ověří, že patří do stejné konverzace. Tím se zachová společná historie bez duplikace.

Přesné omezení a indexy rodičovských vazeb se musí ověřit automatickými testy; nesmí vzniknout cyklický řetězec zpráv ani odkaz do jiné konverzace.

### 3.3 Přílohy a zdroje

**attachments**
- `id`, `conversation_id`, `message_id`, `original_name`
- `storage_path`, `mime_type`, `size_bytes`, `sha256`
- `created_at`

Metadata přílohy se oddělí od obsahu souboru. Samotný soubor se nebude bezdůvodně kopírovat do databáze. Při větvení bude výslovně určeno, zda se příloha dědí z původní zprávy.

**knowledge_sources**
- `id`, `project_id` (NULL pro osobní zdroj), `kind`
- `title`, `storage_path`, `mime_type`, `checksum`
- `created_at`, `updated_at`, `status`

Zdroj musí mít jasný rozsah: osobní nebo konkrétní projekt. Samotná existence zdroje neuděluje oprávnění ke čtení jeho obsahu.

### 3.4 Pracovní poznámky

**notes**
- `id`, `project_id` (NULL pro osobní poznámku)
- `title`, `current_version_id`, `created_at`, `updated_at`, `archived_at`

**note_versions**
- `id`, `note_id`, `version_number`, `content_markdown`
- `created_at`, `change_source`, `change_summary`

Verze jsou neměnné; úprava vytvoří novou verzi. Obnova starší verze vytvoří další verzi s obsahem obnovené verze. Osobní poznámky se automaticky nezpřístupní projektům.

**conversation_sources**
- vazba konverzace/větve na poznámku nebo znalostní zdroj;
- určuje, co může být do konkrétního požadavku připojeno;
- zaznamená také, které zdroje byly skutečně použity při sestavení kontextu.

### 3.5 Profily AI

**ai_profiles**
- `id`, `name`, `description`, `current_version_id`
- `created_at`, `updated_at`, `archived_at`

**ai_profile_versions**
- `id`, `profile_id`, `version_number`
- `instructions`, `default_provider`, `default_model`
- `tool_allowlist_json`, `parameters_json`, `created_at`

Verze profilu se po použití v konverzaci nemění. Zpráva/úloha odkazuje na konkrétní verzi. Profil určuje pracovní roli, nikoli bezpečnostní oprávnění.

### 3.6 Nástroje, oprávnění a schvalování

**tool_definitions**
- `id`, `name`, `description`, `input_schema_json`
- `effect_class` (read_only / write / external / destructive)
- `enabled`, `version`

**permission_policies**
- `id`, `scope_type`, `scope_id`, `subject_type`, `subject_id`
- `capability`, `decision`, `created_at`, `updated_at`

Konkrétní model oprávnění bude ještě upřesněn podle registru nástrojů. Bezpečnostní pravidla jsou centrální a serverová. Profil AI je nesmí rozšířit.

**approval_requests**
- `id`, `task_id`, `conversation_id`, `message_id`
- `tool_name`, `arguments_json`, `arguments_hash`
- `reason`, `risk_level`, `status`
- `requested_at`, `decided_at`, `decided_by`, `decision_reason`

Schválení je vázáno na hash přesných argumentů. Změna argumentů, cíle nebo relevantních oprávnění vyžaduje nové ověření a případně nové schválení. Model nesmí schválit vlastní požadavek.

### 3.7 Úlohy a audit

**tasks**
- `id`, `conversation_id`, `branch_id`, `project_id`
- `profile_version_id`, `status`, `idempotency_key`
- `created_at`, `started_at`, `updated_at`, `finished_at`
- `cancel_requested_at`, `result_json`, `error_json`

**task_events**
- `id`, `task_id`, `event_type`, `payload_json`, `created_at`

**audit_events**
- `id`, `actor_type`, `actor_id`, `action`, `target_type`, `target_id`
- `result`, `details_json`, `created_at`

Stavy úloh vycházejí ze schváleného návrhu A–E: queued, running, waiting_approval, waiting_input, completed, failed, cancel_requested, cancelled, interrupted a recovery_required.

Události úloh a auditní záznamy jsou append-only. Nejasný stav po restartu se označí k obnově/kontrole; nesmí se automaticky opakovat operace s možnými vedlejšími účinky.

## 4. Vztahy a pravidla rozsahu

- Konverzace může být osobní nebo patřit jednomu projektu.
- Zpráva patří do jedné konverzace a jedné větve.
- Větev patří do jedné konverzace; její výchozí kontext může odkazovat na zprávu jiné větve téže konverzace.
- Úloha patří ke konverzaci a případně k její větvi a projektu.
- Poznámka a znalostní zdroj jsou buď osobní, nebo projektové.
- Osobní zdroje se do projektu nepřenášejí automaticky.
- Každý zdroj se při použití znovu autorizuje; historické oprávnění nestačí.
- Smazání projektu nesmí bez výslovného rozhodnutí mazat uživatelské soubory. Výchozí chování má být archivace/odpojení a bezpečné řešení závislých záznamů.
- Mazání větve nesmí odstranit zprávy sdílené s jinými větvemi.
- API klíče a tajné údaje nesmí být obsahem promptů, běžných událostí ani auditních detailů.

## 5. SQLite, integrita a migrace

- Používat jednu hlavní relační databázi pro provozní entity a transakce.
- Zapínat `PRAGMA foreign_keys = ON` při každém připojení k hlavní databázi.
- Nastavit rozumný timeout a jednotný způsob otevírání/uzavírání spojení.
- Vyhodnotit WAL režim a chování souběžných zápisů; nastavit jej až po testu na podporovaných systémech.
- Přidat tabulku `schema_migrations` s verzí, časem a identifikací migrace.
- Migrace musí být verzované, opakovatelné bezpečným způsobem a transakční, pokud to SQLite dovolí.
- Před migrací vytvořit zálohu databáze a ověřit obnovu zálohy.
- Migrace nesmí mazat původní databáze ani soubory; staré zdroje se odstraní až po samostatném schválení a ověření.
- Přidat indexy pro vazby a časté dotazy: project_id, conversation_id, branch_id, parent_message_id, task status/created_at a vazby verzí.
- Všechny SQL dotazy musí používat parametrizované hodnoty.

## 6. Doporučené implementační etapy

Každá etapa bude mít vlastní změny, automatické testy a uživatelský test. Není to pokyn implementovat celý návrh najednou.

1. **Příprava a zálohy:** doplnit testovací základ, popsat umístění a formát existujících dat; připravit migrační mechanismus.
2. **Hlavní databáze a projekty:** vytvořit `mojeai.db`, migrovat projekty a složky z `projects.db`, porovnat počty a obsah záznamů; starou DB ponechat.
3. **Historie:** přidat konverzace a zprávy; chat API začne ukládat a načítat historii. Přestat automaticky ukládat každou otázku a odpověď do dlouhodobé paměti, ale zachovat samostatné ukládání skutečných paměťových záznamů.
4. **Projektový kontext:** propojit konverzace s projekty a ověřovat přístup ke zdrojům.
5. **A – poznámky a zdroje:** nejprve Markdown poznámky a metadata projektových dokumentů; RAG až po ověření správy zdrojů.
6. **B – profily:** profily a verzování, bez možnosti měnit centrální oprávnění.
7. **C – schvalování:** zavést žádosti o schválení a audit ještě před aktivací zápisových nástrojů.
8. **E – úlohy:** persistentní úlohy, události, idempotence a bezpečná obnova.
9. **D – větvení:** až nad stabilní historií a ověřenými rodičovskými vazbami.
10. **Týmová spolupráce modelů:** navázat na profily, úlohy, schvalování a větve.

Pořadí se může po testech upravit. Bez schvalovací vrstvy se nesmí zapnout autonomní zápisové nástroje; bez persistentních úloh se nemají spouštět dlouhé agentní běhy.

## 7. Co se nyní nebude měnit

- Žádný aplikační kód ani databáze uživatele.
- Žádné mazání nebo slučování současných databází.
- Žádná automatická konverze starých záznamů paměti na historii.
- Žádné automatické sdílení osobních dat s projekty.
- Žádné zápisové nástroje ani autonomní příkazy.
- Žádná změna větve `main`.

## 8. Co musí být ověřeno před první migrací

- Čistá instalace vytvoří databázi a tabulky správně.
- Opakované spuštění migrace nezduplikuje ani neztratí data.
- Záloha databáze jde obnovit.
- Po migraci souhlasí počet a obsah projektů a povolených složek.
- Historické soubory paměti zůstanou dostupné.
- Chybné cizí klíče, neplatné ID a pokus o přístup do jiného projektu jsou odmítnuty.
- Restart aplikace nezpůsobí ztrátu ani dvojí provedení úloh.
- Testy ověří mazání projektu, větve a poznámky bez odstranění nesouvisejících dat.

---

**Závěr auditu:** nejbezpečnější cesta je jedna hlavní relační databáze pro projekty a nové provozní entity, zatímco současná sémantická paměť zůstane oddělená, dokud nebude připravená a otestovaná její migrace. Nejdříve se oddělí historie od paměti; teprve potom se na ni navážou A–E.


## 9. Stav první implementační etapy

Dne 25. 11. 2026 byla na pracovní větvi `cleanup/repository-audit` implementována pouze první část databázového základu:

- Nový modul `core/database.py` poskytuje připojení k hlavní SQLite databázi a verzované migrace.
- `data/mojeai.db` je nyní hlavní databází pro projektové záznamy.
- Migrace 1 vytváří tabulky `projects`, `project_folders` a index.
- Migrace 2 importuje existující projekty a povolené složky z `data/projects.db`, zachovává původní číselná ID a otevírá zdrojovou databázi pouze pro čtení.
- Zdrojová `projects.db` se nemaže ani nepřepisuje.
- `ProjectManager` používá hlavní databázi; dosavadní API projektů zůstává beze změny.
- Přidány testy pro čistou instalaci, import projektů a složek, zachování zdroje, opakované spuštění migrace, odmítnutí nekompatibilního schématu a základní CRUD.

**Co zatím implementováno není:** historie konverzací, zprávy, projektové vazby chatů, poznámky, znalostní zdroje, profily, schvalování, úlohy, auditní události ani větvení. Tabulky pro tyto funkce se budou přidávat v dalších samostatných migracích.

**Ověření:** zdrojové soubory a testy byly staticky zkontrolovány. Automatické testy nebylo možné v tomto pracovním prostředí spustit, protože nebylo dostupné připojení ke GitHubu pro stažení pracovní větve. Skutečná migrace uživatelovy databáze nebyla spuštěna. Původní data se proto zatím nijak nezměnila.
