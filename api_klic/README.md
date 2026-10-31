# API klíče

Tato složka obsahuje API klíče pro cloudové providery.

## Struktura

| Soubor | Git? | Obsah |
|---|---|---|
| `gemini.txt.example` | ✅ ano | Šablona s nápovědou |
| `gemini.txt` | ❌ ne (gitignored) | Tvůj skutečný klíč |
| `deepseek.txt.example` | ✅ ano | Šablona |
| `deepseek.txt` | ❌ ne | Tvůj klíč |
| `openai.txt.example` | ✅ ano | Šablona |
| `openai.txt` | ❌ ne | Tvůj klíč |
| `claude.txt.example` | ✅ ano | Šablona |
| `claude.txt` | ❌ ne | Tvůj klíč |

## Jak začít

Pro každý provider, který chceš použít:

```bash
cp gemini.txt.example gemini.txt
# Otevři gemini.txt v editoru, vlož klíč (jen samotný klíč na nový řádek)
```

Klíč musí být **jen na jednom řádku**, bez uvozovek, bez mezer.

## Bezpečnost

- `api_klic/*.txt` je v `.gitignore` - **nikdy se necommitne**
- Před commitem spusť `python kontrola_klicu.py`
- Pokud klíč omylem commitneš, okamžitě si nech vyměnit klíč
u poskytovatele (klíč v git historii = kompromitovaný)

## Odkazy

- Gemini: https://aistudio.google.com/apikey (free tier)
- DeepSeek: https://platform.deepseek.com/
- OpenAI: https://platform.openai.com/api-keys
- Claude: https://console.anthropic.com/

</BDS:create_file>

<BDS:create_file fileName="api_klic/gemini.txt.example">

# Gemini API klíč

# 1. Získej zdarma: https://aistudio.google.com/apikey

# 2. Zkopíruj tento soubor:  cp gemini.txt.example gemini.txt

# 3. Otevři gemini.txt a vlož klíč (jen samotný klíč, bez #)

# Formát klíče: začíná "AIza..."

# Soubor gemini.txt je v .gitignore - nikdy se necommitne.

</BDS:create_file>

<BDS:create_file fileName="api_klic/deepseek.txt.example">

# DeepSeek API klíč

# 1. Získej na: https://platform.deepseek.com/

# 2. Zkopíruj tento soubor:  cp deepseek.txt.example deepseek.txt

# 3. Otevři deepseek.txt a vlož klíč (jen samotný klíč, bez #)

# Formát klíče: začíná "sk-..."

# Soubor deepseek.txt je v .gitignore - nikdy se necommitne.

</BDS:create_file>

<BDS:create_file fileName="api_klic/openai.txt.example">

# OpenAI API klíč

# 1. Získej na: https://platform.openai.com/api-keys

# 2. Zkopíruj tento soubor:  cp openai.txt.example openai.txt

# 3. Otevři openai.txt a vlož klíč (jen samotný klíč, bez #)

# Formát klíče: začíná "sk-proj-..." nebo "sk-..."

# Soubor openai.txt je v .gitignore - nikdy se necommitne.

</BDS:create_file>

<BDS:create_file fileName="api_klic/claude.txt.example">

# Claude (Anthropic) API klíč

# 1. Získej na: https://console.anthropic.com/

# 2. Zkopíruj tento soubor:  cp claude.txt.example claude.txt

# 3. Otevři claude.txt a vlož klíč (jen samotný klíč, bez #)

# Formát klíče: začíná "sk-ant-..."

# Soubor claude.txt je v .gitignore - nikdy se necommitne.

</BDS:create_file>

<BDS:create_file fileName="kontrola_klicu.py">

```python
#!/usr/bin/env python3
"""
Kontrola API klíčů před git commitem.

Projde api_klic/*.txt a upozorní, pokud obsahuje skutečný klíč
(místo prázdného souboru nebo komentářů). Slouží jako poslední
bezpečnostní pojistka před `git commit`.

Použití:
    python kontrola_klicu.py

Návratový kód:
    0 = vše v pořádku
    1 = nalezen skutečný klíč (necommituj!)
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_KLICE_DIR = os.path.join(BASE_DIR, "api_klic")

# Vzory skutečných klíčů podle poskytovatele.
# Cílem je minimalizovat false positives - klíč musí vypadat
# jako skutečný klíč, ne jako šablona.
VZORY = {
    "gemini":   re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "deepseek": re.compile(r"sk-[a-f0-9]{32,}"),
    "openai":   re.compile(r"sk-(proj-)?[A-Za-z0-9_\-]{40,}"),
    "claude":   re.compile(r"sk-ant-[A-Za-z0-9_\-]{40,}"),
}

def zkontroluj_soubor(soubor: str) -> str | None:
    """
    Vrátí název providera, pokud soubor obsahuje skutečný klíč.
    Jinak None.
    """
    cesta = os.path.join(API_KLICE_DIR, soubor)
    provider = soubor[:-4].lower()  # bez ".txt"

    if provider not in VZORY:
        return None

    try:
        with open(cesta, "r", encoding="utf-8", errors="ignore") as f:
            obsah = f.read()
    except Exception as e:
        print(f"⚠️  Nelze číst {soubor}: {e}")
        return None

    if VZORY[provider].search(obsah):
        return provider
    return None

def main() -> int:
    if not os.path.isdir(API_KLICE_DIR):
        print(f"❌ Složka neexistuje: {API_KLICE_DIR}")
        return 1

    problemy = []

    for soubor in sorted(os.listdir(API_KLICE_DIR)):
        if not soubor.endswith(".txt"):
            continue
        provider = zkontroluj_soubor(soubor)
        if provider:
            problemy.append((soubor, provider))

    if problemy:
        print("=" * 60)
        print("❌ POZOR - v api_klic/ jsou SKUTEČNÉ klíče:")
        print("=" * 60)
        for soubor, provider in problemy:
            print(f"   {soubor}  ({provider})")
        print()
        print("Tyto soubory jsou v .gitignore a NESMÍ se commitnout.")
        print()
        print("Pokud už jsou v gitu, okamžitě:")
        print("  1. Vyměň klíč u poskytovatele")
        print("  2. git rm --cached api_klic/<soubor>")
        print("  3. git commit --amend  (nebo git-filter-repo při hlubší historii)")
        return 1

    print("✅ Vše v pořádku - v api_klic/ nejsou žádné skutečné klíče.")
    print("   Můžeš bezpečně commitnout.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

