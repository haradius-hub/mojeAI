@echo off
title MojeAI - Portable AI Assistant
setlocal enabledelayedexpansion

:: ============================================================
::    MOJEAI - Portable AI Assistant
:: ============================================================
echo.
echo ============================================================
echo    MOJEAI - Portable AI Assistant
echo ============================================================
echo.

:: Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Download from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies (may take 5-15 minutes)...
pip install -r requirements.txt --no-warn-script-location > nul 2>&1

:: Start server
echo Starting server...
start /B python app.py > server.log 2>&1

:: Wait for server
echo Waiting for server to start...
timeout /t 3 /nobreak > nul

:: ============================================================
::   SELECT BROWSER
:: ============================================================
echo.
echo ============================================================
echo    SELECT BROWSER
echo ============================================================

:: Detect available browsers
set "pocet=0"
set "volby="

:: Search www folder for browser exe files
for /d %%i in ("www\*") do (
    if exist "%%i\*.exe" (
        for %%f in ("%%i\*.exe") do (
            set /a pocet+=1
            set "browser_!pocet!=%%~nxf"
            set "cesta_!pocet!=%%i\%%~nxf"
            set "volby=!volby! !pocet!"
            echo   !pocet!. %%~nxf
        )
    )
)

:: Add "System browser" option
set /a pocet+=1
set "browser_!pocet!=System browser"
set "cesta_!pocet!=system"
set "volby=!volby! !pocet!"
echo   !pocet!. System browser

:: Add "None - open manually" option
set /a pocet+=1
set "browser_!pocet!=None - open manually"
set "cesta_!pocet!=none"
set "volby=!volby! !pocet!"
echo   !pocet!. None - open manually

echo.
echo ============================================================
echo.

:: If no browser found, skip selection
if %pocet% leq 2 (
    echo No portable browser found.
    echo Opening system browser...
    start http://localhost:5000
    goto :hotovo
)

:: User selection
set "vyber="
set /p "vyber=Enter number (1-%pocet%) or press Enter for first: "

:: If user pressed Enter, select first
if "%vyber%"=="" set "vyber=1"

:: Validate selection
set "platny=0"
for %%v in (%volby%) do (
    if "%vyber%"=="%%v" set "platny=1"
)

if "%platny%"=="0" (
    echo Invalid choice! Using first browser...
    set "vyber=1"
)

:: Get selected browser
call set "browser=%%browser_%vyber%%%"
call set "cesta=%%cesta_%vyber%%%"

echo.
echo ============================================================
echo Launching: %browser%
echo ============================================================

:: Launch selected browser
if "%cesta%"=="system" (
    echo Opening system browser...
    start http://localhost:5000
    goto :hotovo
)

if "%cesta%"=="none" (
    echo.
    echo Open your browser at: http://localhost:5000
    goto :hotovo
)

:: Launch portable browser
if exist "%cesta%" (
    echo Starting %browser%...
    
    :: Special parameters for Chromium/Chrome
    echo %cesta% | findstr /i "chromium chrome" > nul
    if not errorlevel 1 (
        taskkill /f /im "%~nxf" > nul 2>&1
        timeout /t 1 /nobreak > nul
        start "" "%cesta%" --new-window --app=http://localhost:5000 --user-data-dir="%CD%\www\%~nxf\Data"
        goto :hotovo
    )
    
    :: Special parameters for Firefox
    echo %cesta% | findstr /i "firefox librewolf" > nul
    if not errorlevel 1 (
        start "" "%cesta%" -new-window http://localhost:5000
        goto :hotovo
    )
    
    :: Other browsers (Opera, Iron, etc.)
    start "" "%cesta%" http://localhost:5000
    goto :hotovo
) else (
    echo ERROR: Browser not found: %cesta%
    echo Opening system browser...
    start http://localhost:5000
    goto :hotovo
)

:hotovo
echo.
echo ============================================================
echo Server running at: http://localhost:5000
echo To stop, close this window or press Ctrl+C in server.
echo ============================================================
echo.

:: ============================================================
::  THIS KEEPS THE WINDOW OPEN - WAITS FOR A KEY PRESS
:: ============================================================
echo Press any key to exit...
pause > nul
exit /b 0