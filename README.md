# MojeAI - Portable AI asistent s pamětí

Přenosný AI asistent, který běží z jedné složky (ideálně na flashdisku).
Podporuje lokální GGUF modely, Ollamu a cloudová API (Gemini, DeepSeek,
OpenAI, Claude). Má dlouhodobou paměť, volitelný internet, práci s projekty
a bezpečnou editaci souborů (s vynucenou zálohou).

## Stav

**v0.1-original** - funkční prototyp, monolitický `app.py`.

Vývojový plán (tagy v gitu):

| Tag | Fáze | Co přinese |
|---|---|---|
| `v0.1-original` | Baseline | Tato verze |
| `v0.2-refactor` | Refaktor | Rozdělení na `core/`, `routes/`, `static/` |
| `v0.3-projects` | Projekty | Namespacing paměti, oddělení projektů |
| `v0.4-tools` | AI nástroje | Function calling + záloha před zápisem |
| `v0.5-portable` | Portable | Portable Python + venv ve složce |
| `v0.6-ux` | UX | Streaming, markdown, historie konverzací |
| `v0.7-light` | Lehká | sqlite-vec místo ChromaDB, nomic-embed přes llama.cpp |

## Rychlý start

**Windows:**
```

spustit.bat

```
Vyber 1 (CPU) nebo 2 (GPU). Skript nainstaluje závislosti a otevře prohlížeč.

**Linux:**
```bash
./spustit.sh
```

**Ruční spuštění:**

```
pip install -r requirements.txt
python app.py
```

Otevři http://localhost:5000

## API klíče

1. Zkopíruj `api_klic/gemini.txt.example` na `api_klic/gemini.txt`
2. Vlož svůj klíč (jen samotný klíč, bez komentářů)
3. Stejně pro ostatní providery (`deepseek`, `openai`, `claude`)

Soubory `api_klic/*.txt` jsou v `.gitignore` - **nikdy se necommitnou**.
Šablony `.txt.example` se commitují - ty obsahují jen nápovědu.

Před každým commitem zkontroluj:

```
python kontrola_klicu.py
```

## Struktura

```
mojeAI/
├── app.py              ← Flask backend (monolit, fáze 1 ho rozdělí)
├── requirements.txt
├── config.example.json ← šablona konfigurace (commituje se)
├── config.json         ← osobní konfigurace (gitignored)
├── api_klic/           ← API klíče (skutečné .txt gitignored)
├── modely/             ← GGUF modely (gitignored)
├── pamet/              ← vzpomínky (gitignored)
├── data/               ← ChromaDB (gitignored)
├── templates/
│   └── index.html      ← UI
└── www/                ← portable prohlížeče (gitignored)
```

## Bezpečnost

- API klíče **nikdy** necommituj - `kontrola_klicu.py` tě upozorní
- `config.json` obsahuje osobní cesty - je gitignored
- GGUF modely jsou velké (GB) - gitignored
- Před přidáním AI editace souborů bude vynucená záloha + potvrzovací dialog

## Licence

GPLv3 - viz LICENSE.

</BDS:create_file>

<BDS:create_file fileName="GIT_SETUP.md">

```markdown
# Git Setup - MojeAI

Postup pro první commit původní verze jako `v0.1-original`.

## 1. Kontrola před commitem

```bash
python kontrola_klicu.py

Pokud hlásí problém (skutečný klíč v `api_klic/*.txt`), oprav to **před** commitem.

## 2. Inicializace repozitáře

```
cd mojeAI
git init
git branch -M main
```

## 3. Přidání souborů (v tomto pořadí)

Nejdřív `.gitignore`, aby se binárky nepřidaly omylem:

```
git add .gitignore
git add README.md LICENSE GIT_SETUP.md
git add config.example.json
git add www/README.md
git add api_klic/
git add kontrola_klicu.py
```

Zkontroluj, že staged není nic velkého a nic tajného:

```
git status
```

Očekávaný výstup: jen textové soubory, žádné `.gguf`, žádné `.txt` s klíčem.

## 4. Commit baseline

```
git commit -m "v0.1-original: initial portable AI assistant"
git tag v0.1-original
```

## 5. Vytvoření GitHub repozitáře

1. Jdi na https://github.com/new
2. Název: `mojeAI` (nebo jiný)
3. **Nezakládej** README, .gitignore ani LICENSE (už je máš v commitu)
4. Vytvoř repo (může být private)

## 6. Připojení remote a push

```
git remote add origin https://github.com/<tvuj-username>/mojeAI.git
git push -u origin main
git push origin v0.1-original
```

## 7. Co teď máš

- `v0.1-original` tag = zmrazený referenční bod (původní fungující verze)
- `main` branch = můžeš dál vyvíjet
- `api_klic/*.txt` jsou lokální a **nikdy se nepushnou**
- Velké binárky (modely, prohlížeče) nejsou v gitu

## 8. Pokud jsi omylem commitnul klíč

```
# Zjisti, ve kterém commitu:
git log --all --full-history -- api_klic/*.txt

# Pokud je to jen v posledním commitu (a ještě nepushnuto):
git rm --cached api_klic/gemini.txt
git commit --amend

# Pokud je hlouběji v historii nebo už pushnuto:
#  1. Okamžitě si nech vyměnit klíč u poskytovatele
#  2. Použij nástroj git-filter-repo (nebo BFG Repo-Cleaner)
```

**Klíč, který byl kdy v gitu, považuj za kompromitovaný** - i po smazání z historie mohl někdo mít kopii.

## 9. Jak fungují API klíče

- `api_klic/gemini.txt.example` - šablona v gitu (obsahuje jen nápovědu)
- `api_klic/gemini.txt` - tvůj skutečný klíč, **gitignored**

Když klonuješ repo na jiný stroj, musíš udělat:

```
cp api_klic/gemini.txt.example api_klic/gemini.txt
# a vložit klíč
```

## 10. Bezpečnostní tip pro pokročilé

Pokud chceš mít `api_klic/gemini.txt` **trackovaný** (např. chceš ho commitovat prázdný),
ale nechceš, aby se tvůj skutečný klíč omylem commitnul, použij `skip-worktree`:

```
# Po prvním commitu (ještě než vložíš klíč):
git update-index --skip-worktree api_klic/gemini.txt

# Teď můžeš klíč vložit a git ho uvidí jako "beze změny"
# (změny ignoruje, ale při checkoutu ti ho nepřepíše)

# Zrušení:
git update-index --no-skip-worktree api_klic/gemini.txt
```

**Pozor:** Toto je pokročilý trik. Pro běžné použití stačí standardní
pattern `.txt.example` + gitignored `.txt`.

## 11. Co dělat při dalších fázích

Až budeš refaktorovat na moduly:

```
git checkout -b refactor
# pracuj na nové verzi
git commit -m "refactor: split app.py into core/ and routes/"
git checkout main
git merge refactor
git tag v0.2-refactor
git push origin main --tags
```

Stejný pattern pro každou další fázi.

</BDS:create_file>

<BDS:create_file fileName="config.example.json">

```json
{
  "system_prompt": "Jsi užitečný asistent. Odpovídej česky, stručně a výstižně. Používej přirozenou češtinu bez zbytečných formalit.",
  "vychozi_model": "gemini",
  "pristupne_slozky": [],
  "internet": false,
  "max_vzpominek": 5,
  "pocet_souboru_ze_slozky": 10,
  "pouzit_gpu": false,
  "gpu_vrstev": 25
}

