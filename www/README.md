# Portable prohlížeče

Sem umísti portable verze prohlížečů. Launcher (`spustit_cpu.bat`,
`spustit_gpu.bat`, `spustit_en.bat`) je detekuje automaticky podle
`*.exe` v každé podsložce.

## Očekávané složky

- `ChromiumPortable/ChromiumPortable.exe`
- `IronPortable/IronPortable.exe`
- `LibreWolfPortable/LibreWolfPortable.exe`
- `OperaPortable/OperaPortable.exe`

Stačí mít jen ty, které reálně používáš - launcher se přizpůsobí.

## Kde stáhnout

- Chromium Portable: <https://portableapps.com/apps/internet/chromium_portable>
- Iron Portable: <https://portableapps.com/apps/internet/iron_portable>
- LibreWolf Portable: <https://librewolf.net/>
- Opera Portable: <https://portableapps.com/apps/internet/opera_portable>

## Proč nejsou v gitu

Portable prohlížeče mají stovky MB. V `.gitignore` je `www/*/`,
takže se necommitují. Tento README zůstává, aby složka v gitu existovala.
