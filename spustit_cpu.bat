@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title MojeAI - Systemovy Python (CPU)

echo.
echo ============================================================
echo    MOJEAI - SYSTEMOVY PYTHON (CPU)
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [CHYBA] Python nebyl nalezen v PATH.
    echo Nainstaluj Python a povol jeho spousteni z prikazove radky.
    pause
    exit /b 1
)

echo Instaluji zavislosti z requirements.txt...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [CHYBA] Instalace zavislosti selhala.
    pause
    exit /b 1
)

echo.
echo Spoustim server v novem okne...
start "MojeAI - Server (CPU)" /D "%~dp0" cmd /k python app.py

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
set "nazev_!pocet!=Otevru si sam"
echo   !pocet!. Otevru si sam

echo.
set "vyber="
set /p "vyber=Zadej cislo (Enter = prvni): "
if "%vyber%"=="" set "vyber=1"

set "test="
set /a test=%vyber% 2>nul
if not "%test%"=="%vyber%" set "vyber=1"
if %vyber% lss 1 set "vyber=1"
if %vyber% gtr %pocet% set "vyber=1"

set "cesta=!cesta_%vyber%!"
set "nazev=!nazev_%vyber%!"

echo.
echo Spoustim: %nazev%
if "%cesta%"=="system" (
    start "" "http://localhost:5000"
    goto :konec
)
if "%cesta%"=="none" (
    echo Otevri http://localhost:5000
    goto :konec
)
if exist "%cesta%" (
    start "" "%cesta%" "http://localhost:5000"
) else (
    start "" "http://localhost:5000"
)

:konec
echo.
echo Server bezi na http://localhost:5000
echo Pro ukonceni zavri okno serveru.
echo.
pause
