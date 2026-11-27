# Historie konverzací – první databázová etapa

**Stav:** databázové schéma implementováno; API, UI a runtime testy zatím ne  
**Větev:** `cleanup/repository-audit`  
**Migrace:** 3

## Co migrace 3 vytváří

V hlavní databázi `data/mojeai.db` přibývají:

- `conversations` – stabilní textové ID, volitelná vazba na projekt, název a časové značky;
- `messages` – stabilní textové ID, konverzace, volitelná rodičovská zpráva, role, textový obsah a metadata modelu/stavu;
- `attachments` – metadata souborů navázaná na konkrétní zprávu: původní název, relativní úložná cesta, MIME typ, velikost, SHA-256 a čas vytvoření.

Přidány jsou indexy pro seznam konverzací, chronologii zpráv, rodičovské vazby a přílohy.

Rodičovská zpráva je databázově omezena na stejnou konverzaci. Příloha patří konkrétní zprávě; jedna zpráva může mít více příloh. Metadata přílohy jsou oddělena od binárního obsahu souboru.

## Co migrace nedělá

- Nevytváří ani nepřevádí žádnou historii ze staré paměti.
- Nemění `data/pamet.db` ani textové soubory paměti.
- Neukládá skutečné soubory a nepřidává upload/download API.
- Nezavádí seznam, vyhledávání ani opětovné otevírání chatů v UI.
- Nezavádí přetahování souborů, výběr více souborů ani obrazové zpracování.
- Nezavádí větve konverzací; rodičovská vazba je připravena pro návaznost zpráv, nikoli kompletní branching.
- Neprovádí žádnou změnu uživatelské databáze v tomto vývojovém kroku.

## Přílohy a RAW

Schéma dovoluje více záznamů příloh u jedné zprávy a zachovává původní název souboru. Tím neomezuje budoucí podporu běžných dokumentů, obrázků ani fotografických RAW formátů.

Přijetí RAW souboru, jeho bezpečné uložení a případný převod na náhled jsou samostatné kroky. Samotná databázová tabulka nezaručuje, že konkrétní RAW formát umí přečíst vybraný model.

## Testy

Do `tests/test_database.py` byly přidány testy:
- migrace 3 na čisté databázi;
- zachování idempotence všech tří migrací;
- více příloh u jedné zprávy;
- návaznost zprávy na rodiče ve stejné konverzaci;
- odmítnutí rodičovské zprávy z jiné konverzace.

Testy byly přidány do repozitáře, ale v tomto kroku nebyly spuštěny v runtime. Je nutné je spustit lokálně příkazem:

```cmd
python -m unittest discover -s tests -v
```

## Druhá implementační etapa – úložiště konverzací

**Stav:** servisní vrstva přidána; API/UI a runtime testy čekají.

Nový modul `core/conversations.py` poskytuje:
- vytvoření konverzace s volitelným projektem;
- stránkovaný seznam nearchivovaných konverzací s počtem zpráv;
- načtení konverzace včetně zpráv a metadat jejich příloh;
- přidání zprávy s rolí, obsahem, rodičovskou vazbou a metadaty modelu/stavu;
- načtení jednotlivé zprávy.

Vrstva používá hlavní databázi `data/mojeai.db`, parametrizované SQL dotazy, cizí klíče a explicitní zavírání spojení. Nevolá modely, nepřijímá HTTP požadavky a nepracuje s binárním obsahem příloh. Výchozí chování tak zůstává oddělené od existujícího chatového endpointu a dlouhodobé paměti.

Nové testy v `tests/test_conversations.py` pokrývají vytvoření a načtení konverzace, zprávy, stránkování, metadata příloh, odmítnutí rodiče z jiné konverzace a validaci vstupů. Testy jsou přidány, ale musí se spustit v lokálním prostředí.


## Třetí implementační etapa – napojení chatového API na historii

**Stav:** implementováno na pracovní větvi; runtime testy čekají.

- Endpoint `POST /api/chat` přijímá volitelné `conversation_id` v JSON i multipart požadavku.
- Pokud ID chybí, vytvoří se nová konverzace s názvem odvozeným od první otázky (případně názvu souboru).
- Uživatelská zpráva se uloží před voláním modelu. Následující uživatelská zpráva se naváže na předchozí odpověď; odpověď modelu je potomkem aktuální uživatelské zprávy.
- Odpověď ukládá model, poskytovatele, dobu generování a stav. Výjimka modelu i chybová odpověď poskytovatele se evidují jako `failed`.
- API vrací `conversation_id`, ID obou nových zpráv a stav odpovědi.
- Chatové UI předává vrácené ID při dalších zprávách v rámci aktuálně otevřené stránky. Po obnovení stránky zatím neumí načíst historii ani znovuotevřít dřívější konverzaci.
- Stávající dlouhodobá paměť zůstává beze změny a oddělená od historie.
- Binární přílohy ani jejich metadata se v této etapě do historie neukládají; jejich trvalé úložiště a vícesouborový upload zůstávají samostatným úkolem.
- Přidán `tests/test_chat_api.py` pro první/ navazující zprávu, chybu modelu a neexistující ID. Testy zatím nebyly spuštěny v runtime.

