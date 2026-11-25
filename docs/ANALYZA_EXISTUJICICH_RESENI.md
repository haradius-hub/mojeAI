# Analýza existujících řešení a rozšíření koncepce mojeAI

Datum: 25. 11. 2026  
Pracovní větev: `cleanup/repository-audit`  
Stav: koncepční analýza; nejde o implementaci.

## 1. Účel dokumentu

Cílem není nahradit mojeAI jinou aplikací ani provozovat několik chatovacích aplikací vedle sebe. Cílem je prozkoumat již existující řešení, převzít ověřené principy a vhodně je začlenit do jediné aplikace mojeAI.

mojeAI zůstává vlastní aplikační a orchestrace vrstvou nad lokálními i cloudovými modely. Nemá znovu implementovat modelové backendy, například Ollamu. Její hlavní hodnotou je jednotné pracovní prostředí: modely, historie, projekty, paměť, soubory, nástroje, schvalování a spolupráce.

Tento dokument rozšiřuje koncepční návrh o pět oblastí A–E. Před implementací je nutné porovnat návrh se skutečným stavem kódu a navrhnout konkrétní databázové/API změny.

## 2. Zásady návrhu

1. **Jedna aplikace:** všechny funkce jsou součástí mojeAI; externí projekty slouží jako inspirace, nikoli jako další povinné aplikace.
2. **Modelová nezávislost:** profily, projekty, poznámky a historie nejsou vlastnictvím konkrétního poskytovatele.
3. **Oddělení datových vrstev:** konverzace, osobní paměť, projektová paměť, poznámky a dokumentová znalostní báze mají odlišný účel a nesmějí se bez kontroly slévat.
4. **Oprávnění před schopnostmi:** nástroj může provést pouze operaci, kterou dovolují pravidla aplikace a projektu.
5. **Člověk rozhoduje o vedlejších účincích:** zápisy, mazání, příkazy a změny externích systémů podléhají schvalovací politice.
6. **Dohledatelnost:** aplikace rozlišuje návrh modelu, požadavek na nástroj, schválení, skutečné provedení a ověřený výsledek.
7. **Postupné dodávání:** každá funkce musí mít samostatný rozsah, testy a možnost bezpečného vypnutí.

## 3. Co již nabízejí jiné projekty

### 3.1 Open WebUI

Z oficiální dokumentace stojí za pozornost:

- **Notes:** trvalé poznámky mimo jednotlivé chaty, možnost připojit celý text poznámky ke konverzaci a AI nástroje pro vyhledání, čtení, vytvoření a úpravu poznámek.
- **Knowledge:** dokumentové znalostní báze, jednotlivé soubory a možnost připojit je ke konkrétnímu chatu, složce nebo modelu.
- **Workspace / Models:** opakovaně použitelné modelové profily kombinující základní model, systémové instrukce, znalosti, nástroje a dovednosti.
- **Channels:** společný prostor, ve kterém lze modely vyvolat pomocí `@model`; modelové odpovědi mohou být součástí sdílené konverzace.

Zdroje:
- https://docs.openwebui.com/features/notes/
- https://docs.openwebui.com/features/workspace/
- https://docs.openwebui.com/features/workspace/knowledge/
- https://docs.openwebui.com/features/channels/

### 3.2 LibreChat

Z oficiální dokumentace stojí za pozornost:

- **Projects:** seskupení souvisejících chatů se sdílenými instrukcemi a referenčními soubory.
- **Agents:** opakovaně použitelné profily s vlastními instrukcemi, soubory a nástroji.
- **Tool approval / Ask User:** běh agenta se může pozastavit, zobrazit uživateli požadovanou akci a pokračovat až po rozhodnutí.
- **Forking Chats:** vytvoření nové větve konverzace od vybrané zprávy bez změny původního rozhovoru.
- **Background Agent Responses:** dlouhotrvající požadavky mají identifikátor, stav, možnost kontroly, zastavení a obnovy. Schvalovací požadavky mohou běh pozastavit.
- **Message Search:** vyhledávání v obsahu starších konverzací.

Zdroje:
- https://www.librechat.ai/docs/features
- https://www.librechat.ai/docs/features/agents
- https://www.librechat.ai/docs/features/fork
- https://www.librechat.ai/docs/features/background_responses

### 3.3 AnythingLLM

Z dokumentace je užitečný zejména rozdíl mezi:

- dokumentem přiloženým pouze ke konkrétnímu vláknu,
- dokumentem vloženým do pracovního prostoru, a tedy dostupným napříč jeho vlákny.

To je dobrý vzor pro rozlišení dočasné přílohy a trvalého projektového zdroje.

Zdroj:
- https://docs.anythingllm.com/chatting-with-documents/introduction

### 3.4 Další inspirace pro větvení

Pro samotný strom konverzací existují i specializované projekty, například:
- https://github.com/Kylejeong2/synapse
- https://github.com/arichyx/fork-chat

Tyto projekty jsou inspirací pro datový model větví a zobrazení stromu, nikoli doporučením přebírat jejich technologický stack.

## 4. Navrhovaná rozšíření A–E

## A. Pracovní poznámky a znalostní báze

### Účel

Umožnit uchovávat informace, které mají hodnotu i mimo konkrétní chat: technickou dokumentaci, provozní postupy, rozhodnutí, poznámky, výzkum, koncepty a pracovní taháky.

### Rozlišení čtyř typů obsahu

1. **Příloha konverzace:** dočasný soubor připojený k jednomu požadavku nebo vláknu.
2. **Projektový dokument:** soubor připojený k projektu a dostupný v jeho konverzacích podle oprávnění.
3. **Pracovní poznámka:** editovatelný text/Markdown, který žije samostatně a lze jej připojit ke konverzacím.
4. **Znalostní báze:** větší sada dokumentů indexovaná pro vyhledávání relevantních pasáží (RAG); nemá se automaticky posílat celá do každého promptu.

Osobní paměť zůstává samostatnou vrstvou. Poznámka není automaticky vzpomínka a dokument není automaticky instrukce.

### Požadované funkce

- Vytvořit, upravit, přejmenovat, archivovat a odstranit poznámku.
- Organizovat poznámky do projektů, složek a případně stránek/podstránek.
- Vyhledávat podle názvu i obsahu.
- Připnout důležité poznámky.
- Připojit poznámku nebo dokument ke konkrétnímu chatu.
- Zobrazit, které zdroje byly skutečně použity při odpovědi.
- Umožnit AI navrhnout úpravu poznámky; přímý zápis podléhá oprávněním a schvalovací politice.
- Udržovat historii změn a možnost obnovit předchozí verzi.
- Exportovat poznámky alespoň do Markdownu a TXT; další formáty podle možností aplikace.

### Pravidla kontextu

- Projektové zdroje jsou dostupné jen v daném projektu.
- Osobní poznámky nejsou automaticky viditelné v každém projektu.
- Před odesláním promptu aplikace sestaví přehledný seznam použitých zdrojů.
- Uživatel může zkontrolovat a odebrat zdroj z konkrétního požadavku.
- RAG výsledek musí zachovat identifikaci zdroje a pokud možno stránku/sekci.

### Akceptační kritéria

- Poznámka existuje nezávisle na chatu a lze ji znovu použít v jiném chatu.
- Projektový dokument není dostupný v jiném projektu bez výslovného sdílení.
- Příloha jednoho chatu se nestane automaticky trvalým projektovým dokumentem.
- Uživatel vidí, které poznámky/dokumenty byly použity jako kontext.

## B. Profily AI a pracovní role

### Účel

Uložit opakovaně použitelné pracovní konfigurace AI, aby uživatel nemusel při každém chatu znovu nastavovat instrukce, nástroje a požadovaný způsob práce.

### Profil není model

Profil/role je oddělen od poskytovatele a konkrétního modelu. Například role „Linuxový administrátor“ může být přiřazena Gemini, DeepSeek nebo lokálnímu modelu. Při změně modelu zůstává profil zachován, pokud nový model podporuje požadované schopnosti.

### Příklady profilů

- Obecný asistent.
- Linuxový administrátor.
- Programátor.
- Nezávislý auditor kódu.
- Analytik dokumentů.
- Technický dokumentarista.
- Bezpečnostní kontrolor.

### Nastavení profilu

- Název, popis a systémové instrukce.
- Výchozí model nebo pravidlo výběru modelu.
- Povolené nástroje.
- Přístup ke globálním a projektovým zdrojům.
- Oprávnění pro čtení/zápis/spouštění.
- Požadavek na schválení jednotlivých kategorií operací.
- Parametry modelu, pokud je poskytovatel podporuje.
- Verze profilu a historie úprav.

### Bezpečnostní pravidla

- Profil nemůže sám udělit oprávnění, která uživatel nebo projekt nepovolil.
- Systémová bezpečnostní pravidla mají přednost před instrukcemi profilu.
- Změna profilu nesmí potichu změnit oprávnění již běžící úlohy.
- Aplikace má zobrazit, který profil a model právě odpovídají.

### Akceptační kritéria

- Uživatel vytvoří profil a znovu jej použije v jiném chatu.
- Profil lze použít s jiným kompatibilním modelem bez přepsání jeho identity.
- Přidělené nástroje a oprávnění jsou viditelné a kontrolovatelné.
- Profil nemůže obejít globální ani projektová bezpečnostní pravidla.

## C. Schvalovací centrum

### Účel

Jedno místo, kde uživatel vidí operace, které AI navrhla a které vyžadují rozhodnutí. Schválení nesmí být skryté v dlouhém textu konverzace.

### Kategorie operací

- Zápis nebo úprava souboru.
- Mazání nebo přesun souboru.
- Spuštění příkazu.
- Git operace měnící pracovní strom nebo vzdálený repozitář.
- Změna konfigurace či nastavení.
- Externí akce, například odeslání zprávy nebo změna záznamu přes API.

### Obsah žádosti o schválení

- Kdo/ který model akci navrhl.
- Projekt, konverzace a úloha, ze které požadavek pochází.
- Název nástroje a přesné argumenty.
- Důvod a očekávaný výsledek.
- Dotčené soubory nebo systémy.
- Náhled diffu, pokud se mění soubor.
- Riziková úroveň a případné nevratné důsledky.
- Čas vytvoření a stav žádosti.

### Rozhodnutí

- Schválit.
- Zamítnout.
- Upravit argumenty a následně schválit, pokud je daný nástroj bezpečně editovatelný.
- Zrušit nebo nechat žádost vypršet.

### Zásadní bezpečnostní pravidla

- Model nesmí schválit vlastní požadavek.
- Schválení je vázáno na přesný obsah operace; změna argumentů vyžaduje nové schválení.
- Po schválení se znovu ověří oprávnění a existence cíle.
- Změna oprávnění nebo projektu může čekající žádost zneplatnit.
- Aplikace musí zaznamenat rozhodnutí i skutečný výsledek.
- Zamítnutí nesmí být interpretováno jako úspěšné provedení.
- Opakovaný požadavek nesmí bez kontroly způsobit dvojí provedení.

### Akceptační kritéria

- Zápis souboru nelze provést bez požadovaného schválení.
- Uživatel před schválením vidí přesné změny.
- Po zamítnutí se operace neprovede.
- Auditní záznam rozlišuje navrženo, schváleno, spuštěno, dokončeno a selhalo.

## D. Větvení konverzací

### Účel

Umožnit experimentovat s alternativním pokračováním rozhovoru, aniž by se zničila původní konverzace. Užitečné při porovnávání modelů, návrhů, oprav kódu a různých řešení.

### Chování

- Uživatel vybere zprávu a vytvoří z ní novou větev.
- Původní větev zůstane beze změny.
- Nová větev zdědí kontext až po vybranou zprávu.
- Uživatel může větev pojmenovat a přepínat mezi větvemi.
- Větve lze zobrazit jako jednoduchý strom nebo seznam alternativ.
- Větev může používat jiný model nebo profil.
- Uživatel může porovnat odpovědi a případně zkopírovat vybrané pokračování do hlavní větve.

### Přílohy a zdroje

Při větvení musí být jasné, zda se přenášejí přílohy, projektové zdroje a aktivní profil. Uživatel má mít možnost vyloučit velké nebo problematické přílohy. Oprávnění se nikdy nedědí pouze z historického stavu: při použití zdroje se znovu ověří aktuální přístup.

### Datový návrh

Konverzace by neměla být ukládána jen jako jeden lineární text. Zprávy potřebují stabilní ID a vazbu na rodičovskou zprávu nebo větev. Historie pak může reprezentovat strom bez kopírování všech zpráv při každém odbočení. Konkrétní schéma se navrhne až po auditu stávající databáze a chatového API.

### Akceptační kritéria

- Větev vznikne od vybrané zprávy.
- Původní konverzace se nezmění.
- Každá větev má správný kontext a vlastní pokračování.
- Smazání jedné větve neodstraní sdílené předchozí zprávy ani jiné větve.
- Uživatel pozná, ve které větvi právě pracuje.

## E. Přehled úloh a běžících operací

### Účel

Dlouhá práce AI nesmí být závislá na tom, že uživatel nechá otevřené jedno okno chatu. Aplikace musí evidovat úlohu jako samostatnou jednotku práce a zobrazit její stav.

### Příklady úloh

- Analýza větší sady dokumentů.
- Procházení repozitáře a audit kódu.
- Zpracování více souborů.
- Spolupráce několika modelů.
- Dlouhé generování nebo vykonávání povoleného nástroje.
- Příprava změn a testovací dávky.

### Stavový model

Doporučené stavy:

- `queued` – čeká ve frontě.
- `running` – právě probíhá.
- `waiting_approval` – čeká na rozhodnutí uživatele.
- `waiting_input` – čeká na doplňující informaci.
- `completed` – úspěšně dokončeno.
- `failed` – selhalo.
- `cancel_requested` – uživatel požádal o zastavení.
- `cancelled` – zastavení potvrzeno.
- `interrupted` – proces byl přerušen a výsledek není dokončen.
- `recovery_required` – stav vyžaduje kontrolu; aplikace nesmí automaticky spustit neznámou operaci znovu.

### Informace o úloze

- Jedinečné ID a název.
- Projekt, konverzace a případná větev.
- Použitý model/profil nebo seznam spolupracujících modelů.
- Čas zahájení, poslední aktualizace a dokončení.
- Aktuální fáze a průběžné zprávy.
- Použité nástroje a jejich výsledky.
- Čekající schválení.
- Výstup, chyby a možnost navázat na výsledek.
- Možnost požádat o zastavení.

### Odolnost a bezpečnost

- Stav úlohy musí být uložen v databázi, ne pouze v paměti webového procesu.
- Každý požadavek má idempotency key nebo jinou ochranu proti nechtěnému dvojímu spuštění.
- Ztráta spojení s prohlížečem nesmí sama o sobě znamenat ztrátu úlohy.
- Po restartu aplikace musí být možné rozlišit dokončené, bezpečně obnovitelné a neznámé operace.
- Neznámá operace se nesmí automaticky opakovat, pokud mohla mít externí vedlejší účinek.
- Zastavení je žádost o kooperativní přerušení; aplikace musí zobrazit potvrzený konečný stav.
- Již dokončené externí akce se zastavením nevracejí zpět.

### Akceptační kritéria

- Uživatel zavře nebo obnoví stránku a stále vidí evidovanou úlohu.
- Úloha zobrazuje aktuální stav a historii kroků.
- Čekající schválení je dostupné z přehledu úloh i z konverzace.
- Zastavení se hlásí jako požadované, dokud není potvrzeno.
- Po restartu aplikace se neznámá operace automaticky neopakuje.

## 5. Společná architektura A–E

Funkce A–E nemají vznikat jako pět izolovaných modulů. Potřebují sdílené vazby na projekty, konverzace, zprávy, profily a oprávnění.

### Doporučené logické entity

- **Project** – pracovní prostor a jeho pravidla.
- **Conversation** – konverzace v projektu nebo globálním prostoru.
- **Message** – zpráva se stabilním ID a případnou rodičovskou vazbou.
- **ConversationBranch** – větev konverzace.
- **Note** – trvalá pracovní poznámka.
- **KnowledgeSource** – dokument nebo zdroj znalostní báze.
- **AIProfile** – modelově nezávislá role/instrukce.
- **ToolDefinition** – definice dostupného nástroje.
- **PermissionPolicy** – oprávnění v globálním a projektovém rozsahu.
- **ApprovalRequest** – žádost o schválení konkrétní operace.
- **Task / TaskEvent** – dlouhodobá úloha a její události.
- **AuditEvent** – dohledatelný záznam důležitých operací.

Jde o logický návrh, nikoli hotové databázové schéma. Před implementací se musí porovnat se současnou SQLite databází a moduly `core/projects.py`, `core/memory.py` a chatovými routami.

### Společné zásady

- Každý záznam má stabilní ID.
- Záznamy, které patří do projektu, mají explicitní `project_id`.
- Globální záznam má jasně definovaný globální rozsah; nesmí vzniknout nejednoznačnost z chybějící hodnoty.
- Každá operace ověřuje oprávnění na serveru, nikoli jen v UI.
- Obsah souborů, poznámek, repozitářů a výstupů nástrojů je nedůvěryhodný vstup, nikoli instrukce s vyšší prioritou.
- Změny schématu databáze vyžadují verzované migrace a zálohu.
- Aplikace zaznamenává čas odpovědi, model, poskytovatele a pokud možno tokeny a rychlost generování, aniž by ukládala tajné klíče do historie.

## 6. Doporučené pořadí implementace

Pět rozšíření je schváleno jako součást cílové koncepce, nikoli jako pokyn implementovat je najednou.

1. **Nejdříve stabilizace současného základu:** dokončit praktické testy souborů a instalačních cest, přidat základní automatické testy a ověřit aktuální databázi.
2. **Společný datový základ:** propojit projekty, konverzace, zprávy a kontext. Rozhodnout o verzování databáze a migracích.
3. **A – Poznámky a zdroje:** začít jednoduchými Markdown poznámkami a projektovými dokumenty; RAG znalostní bázi přidat jako samostatnou navazující část.
4. **B – Profily AI:** zavést modelově nezávislé profily, ale oprávnění ponechat v centrální bezpečnostní vrstvě.
5. **C – Schvalovací centrum:** nejprve pro zápisy a příkazy; bez něj nezapínat autonomní změny souborů.
6. **E – Evidence úloh:** zavést persistentní stav úloh a jejich událostí před rozsáhlejšími agentními běhy a týmovou spoluprací.
7. **D – Větvení konverzací:** implementovat po stabilizaci modelu zpráv a historie.
8. **Navázat týmovou spoluprací modelů:** použít profily, úlohy, schvalování a větve jako již existující stavební bloky.

Pořadí C/E/D lze upravit podle výsledku technického auditu; zásadní je, aby bezpečnostní schvalování existovalo před nástroji, které mění data, a aby dlouhé úlohy měly trvalou evidenci.

## 7. Co zatím neimplementovat

- Žádné automatické přepisování souborů bez schválení.
- Žádné neomezené spouštění shellu.
- Žádné automatické sdílení osobních poznámek do projektů.
- Žádné automatické spouštění úlohy znovu po nejasném výsledku.
- Žádné složité vizuální grafy větvení, dokud nebude ověřen datový model.
- Žádný druhý agentní runtime jen kvůli inspiraci z jiného projektu.
- Žádná závislost na jediné externí chatovací aplikaci.

## 8. Další krok

Než se začne implementovat, provést cílený audit aktuálního kódu a databáze:

1. Zmapovat současné tabulky SQLite a jejich inicializaci/migrace.
2. Projít `core/projects.py`, `core/memory.py`, `routes/projects.py`, `routes/chat.py` a frontend.
3. Zjistit, které části A–E už mají částečný základ.
4. Navrhnout minimální datový model a API bez zbytečného redesignu.
5. Rozdělit práci na malé, samostatně testovatelné etapy.

Veškeré změny zůstávají na `cleanup/repository-audit`. Větev `main` se nemění bez výslovného souhlasu uživatele.
