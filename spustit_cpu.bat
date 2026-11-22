@echo off
title MojeAI - Přenosný AI asistent (CPU)
setlocal enabledelayedexpansion

:: ============================================================
::    MOJEAI - Přenosný AI asistent (CPU verze)
:: ============================================================
echo.
echo ============================================================
echo    MOJEAI - Přenosný AI asistent (CPU verze)
echo ============================================================
echo.

:: Kontrola Pythonu
python --version > nul 2>&1
if errorlevel 1 (
    echo CHYBA: Python neni nainstalovany!
    echo Stahni si ho z https://python.org
    pause
    exit /b 1
)

:: Instalace zavislosti
echo.
echo ============================================================
echo   INSTALACE ZAVISLOSTI (CPU verze)
echo ============================================================
echo Instaluji zavislosti (muze to trvat 5-10 minut)...
pip install -r requirements.txt --no-warn-script-location

if errorlevel 1 (
    echo.
    echo CHYBA: Instalace selhala!
    pause
    exit /b 1
)

:: Spusteni serveru
echo.
echo ============================================================
echo   SPOUSTENI SERVERU
echo ============================================================
echo Spoustim server v novem okne...
start "MojeAI - Server (CPU)" cmd /k python app.py

:: Cekani na server
echo Cekam na nastartovani serveru (8 sekund)...
timeout /t 8 /nobreak > nul

:: ============================================================
::   VYBER PROHLIZECE
:: ============================================================
echo.
echo ============================================================
echo    VYBER PROHLIZECE
echo ============================================================

set "pocet=0"

for /d %%i in ("www\*") do (
    if exist "%%i\*.exe" (
        for %%f in ("%%i\*.exe") do (
            set /a pocet+=1
            set "cesta_!pocet!=%%f"
            set "nazev_!pocet!=%%~nxf"
            echo   !pocet!. %%~nxf
        )
    )
)

set /a pocet+=1
set "cesta_!pocet!=system"
set "nazev_!pocet!=Systemovy prohlizec"
echo   !pocet!. Systemovy prohlizec

set /a pocet+=1
set "cesta_!pocet!=none"
set "nazev_!pocet!=Zadny - otevru si sam"
echo   !pocet!. Zadny - otevru si sam

echo.
echo ============================================================
echo.

set "vyber="
set /p "vyber=Zadej cislo (1-%pocet%) nebo Enter pro prvni: "

if "%vyber%"=="" set "vyber=1"

set "test="
set /a test=%vyber% 2>nul
if not "%test%"=="%vyber%" (
    echo Neplatna volba! Pouzivam prvni...
    set "vyber=1"
)

if %vyber% lss 1 set "vyber=1"
if %vyber% gtr %pocet% set "vyber=1"

set "cesta=!cesta_%vyber%!"
set "nazev=!nazev_%vyber%!"

echo.
echo ============================================================
echo Spoustim: %nazev%
echo ============================================================

if "%cesta%"=="system" (
    start http://localhost:5000
    goto :konec
)

if "%cesta%"=="none" (
    echo Otevri si prohlizec na: http://localhost:5000
    goto :konec
)

if exist "%cesta%" (
    echo Spoustim %nazev%...
    start "" "%cesta%" http://localhost:5000
    goto :konec
)

start http://localhost:5000

:konec
echo.
echo ============================================================
echo Server bezi na: http://localhost:5000
echo Pro ukonceni zavri okno serveru.
echo ============================================================
echo.
pause