# Historie konverzací – první databázová etapa

**Stav:** databázové schéma implementováno; API je napojeno, uživatelská historie a runtime API testy čekají  
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

**Stav:** servisní vrstva přidána; API napojeno ve třetí etapě, uživatelská historie a runtime API testy čekají.

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
- Příjem `.htm`, `.html`, `.css` a `.js` je doplněn do stávajícího uploadu. Obsah se předává modelu jako text pro analýzu; kód se nevykonává. Souběžná analýza více souborů a izolovaný náhled/spuštění HTML aplikace zůstávají plánované.
- Přidán `tests/test_chat_api.py` pro první/ navazující zprávu, chybu modelu a neexistující ID. Testy zatím nebyly spuštěny v runtime.



## Čtvrtá implementační etapa – kontext, přílohy a uživatelská historie

**Stav:** implementováno na pracovní větvi; automatické testy doplněny, lokální runtime ověření této etapy čeká.

- Migrace 4 přidává sloupce is_pinned a pin_order. Výchozí hodnoty zachovají všechny dosavadní konverzace jako nepřipnuté.
- Seznam konverzací řadí připnuté chaty podle ručně spravovaného pin_order a běžné chaty podle poslední aktivity. Aktivita připnutého chatu pořadí nemění.
- Připnutí a odepinutí udržuje souvislé pořadí; API odmítne neúplný nebo duplicitní seznam při změně pořadí.
- Přidán textový vyhledávací dotaz nad názvy konverzací a obsahem zpráv.
- Chat API poskytuje seznam, detail konverzace, připnutí, změnu pořadí a stažení příloh.
- Chatové UI má výchozí sekci Konverzace, přepínač Nastavení, tlačítko Nový chat, vyhledávání, otevření starších chatů a ovládání připnutí. Připnuté položky lze přetahovat myší; při aktivním vyhledávání je přetahování vypnuto, aby se neposílal neúplný seznam pořadí.
- Model dostává nejvýše 12 posledních zpráv. Textový limit je nejvýše 24 000 znaků; pro lokální modely se snižuje podle nastavení n_ctx. Historie v databázi se nezkracuje ani nemaže.
- Přílohy se ukládají do data/uploads/<conversation_id>/, jejich metadata se ukládají do tabulky attachments a jsou navázána na uživatelskou zprávu. Limit jednoho uploadu je 25 MB.
- Při pokračování se podporované starší textové a kancelářské přílohy znovu načítají z trvalého úložiště do omezeného kontextu.
- API při vracení detailu konverzace nezveřejňuje interní úložné cesty ani SHA-256. Samostatný endpoint poskytuje stažení přílohy.
- Opraveno ukládání přepínače internetu: UI nyní kontroluje HTTP status i aplikační status odpovědi serveru.

### Doplněné automatické testy

- Migrace 4 zachová existující konverzace a nastaví výchozí stav připnutí.
- Připnuté chaty drží pořadí i po nové aktivitě; změna pořadí a odepinutí přepočítají pořadí.
- Vyhledávání najde konverzaci podle názvu i obsahu zprávy.
- Metadata příloh a omezené chronologické načtení posledních zpráv jsou pokryty testy.
- Chat API testy ověřují vložení předchozích zpráv do promptu, trvalé uložení přílohy a API seznamu/připnutí/pořadí.

### Co zůstává mimo tuto etapu

- Větvení konverzací není implementováno; rodičovské vazby zpráv stále nejsou plnohodnotným stromem větví.
- Připojování konverzací k projektům, více souborů v jedné zprávě, obrázkové vstupy, drag-and-drop upload a bezpečný HTML preview zůstávají samostatnými úkoly.
- Detail konverzace se nyní načítá celý; serverový kontext modelu je omezený samostatně. Stránkování dlouhého zobrazení historie lze doplnit podle praktického testu.
- Automatické testy nebyly v tomto vývojovém prostředí spuštěny. Je nutné je spustit v uživatelově Windows portable instalaci.
