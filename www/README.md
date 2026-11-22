# Portable prohlizece

Do podslozek teto slozky lze umistit portable verze prohlizecu. Pouziti je volitelne.

Aktualne je automaticky nabizi pouze Windows launcher `spustit_cpu.bat` (systemovy Python). Portable rezim spousteny pres `run.py` otevre vychozi systemovy prohlizec. GPU launcher je vypnuty a historicky `spustit_en.bat` neni doporucenou cestou.

## Ocekavane slozky

- `ChromiumPortable/ChromiumPortable.exe`
- `IronPortable/IronPortable.exe`
- `LibreWolfPortable/LibreWolfPortable.exe`
- `OperaPortable/OperaPortable.exe`

Nazvy podslozek a spustitelnych souboru se mohou podle konkretni distribuce lisit. Launcher prohledava podslozky `www/` a nabidne nalezene soubory `*.exe`.

## Kde hledat

- Chromium Portable: <https://portableapps.com/apps/internet/chromium_portable>
- Iron Portable: <https://portableapps.com/apps/internet/iron_portable>
- LibreWolf: <https://librewolf.net/>
- Opera Portable: <https://portableapps.com/apps/internet/opera_portable>

## Proc nejsou v Gitu

Portable prohlizece mohou zabirat stovky MB. V `.gitignore` je proto nastavena vyjimka `www/*/`; tento README zustava verzovany, aby slozku popsal.
