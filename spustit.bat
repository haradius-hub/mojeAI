@echo off
title MojeAI - Přenosný AI asistent

echo.
echo ============================================================
echo    MOJEAI - Přenosný AI asistent
echo ============================================================
echo.
echo   1. CPU verze (rychla instalace, bez GPU)
echo   2. GPU verze (detekce GPU + instalace)
echo.
echo ============================================================
echo.

set "volba="
set /p "volba=Vyber (1/2) nebo Enter pro CPU: "

if "%volba%"=="2" (
    echo Spoustim GPU verzi...
    start "" "spustit_gpu.bat"
) else (
    echo Spoustim CPU verzi...
    start "" "spustit_cpu.bat"
)

exit /b 0