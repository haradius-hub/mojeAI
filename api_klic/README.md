# API klíče

MojeAI podporuje klíče pro tyto cloudové poskytovatele:

- Gemini
- DeepSeek
- OpenAI
- Claude (Anthropic)

## Uložení klíče

Nejjednodušší postup:

1. Spusť MojeAI lokálně.
2. V postranním panelu vyber příslušného cloudového poskytovatele.
3. Do pole **API klíč pro zvolený model** vlož klíč.
4. Klikni na **Uložit klíč**.

Aplikace uloží klíč do souboru `api_klic/<provider>.txt`.

Klíč lze uložit také ručně. Vytvoř například `gemini.txt` v této složce a vlož do něj pouze samotný klíč, bez uvozovek a komentářů. Pro další poskytovatele použij názvy `deepseek.txt`, `openai.txt` nebo `claude.txt`.

## Bezpečnost

- Skutečné soubory `api_klic/*.txt` jsou uvedeny v `.gitignore`.
- Nikdy necommituj skutečný API klíč ani jej neposílej v issue, logu nebo veřejné konverzaci.
- Před commitem lze spustit `python kontrola_klicu.py`. Jde pouze o doplňkovou kontrolu známých formátů klíčů.
- Pokud se klíč dostane do Gitu nebo na veřejnost, zneplatni jej u poskytovatele a vytvoř nový.
- Klíče se ukládají lokálně v souborech; chraň proto celý adresář aplikace a zálohy.

## Získání klíče

- Gemini: https://aistudio.google.com/apikey
- DeepSeek: https://platform.deepseek.com/
- OpenAI: https://platform.openai.com/api-keys
- Claude: https://console.anthropic.com/

Soubory `*.txt.example` v repozitáři jsou v současnosti prázdné zástupné soubory. Neobsahují klíče ani úplný návod; tento README je zdrojem instrukcí.
