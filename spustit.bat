@echo off
setlocal
cd /d "%~dp0"
title MojeAI - Spusteni

echo.
echo ============================================================
echo    MOJEAI - SPUSTENI
echo ============================================================
echo.
echo   1. Portable Python (doporuceno)
echo   2. Systemovy Python (CPU)
echo   3. Konec
echo.
echo GPU instalace zatim neni podporovana.
echo ============================================================
echo.

set "volba="
set /p "volba=Vyber (1-3), Enter = portable: "
if "%volba%"=="" set "volba=1"

if "%volba%"=="1" goto :portable
if "%volba%"=="2" goto :system
if "%volba%"=="3" exit /b 0

echo Neplatna volba.
pause
exit /b 1

:portable
call setup_portable.bat
if errorlevel 1 exit /b 1
if not exist "python\python.exe" (
    echo [CHYBA] Portable Python nebyl nalezen.
    pause
    exit /b 1
)
"python\python.exe" run.py
exit /b %errorlevel%

:system
call spustit_cpu.bat
exit /b %errorlevel%
