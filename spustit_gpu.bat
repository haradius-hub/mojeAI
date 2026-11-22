@echo off
title MojeAI - Přenosný AI asistent (GPU)
setlocal enabledelayedexpansion

:: ============================================================
::    MOJEAI - Přenosný AI asistent (GPU verze)
:: ============================================================
echo.
echo ============================================================
echo    MOJEAI - Přenosný AI asistent (GPU verze)
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

:: ============================================================
::   DETEKCE GPU
:: ============================================================
echo.
echo ============================================================
echo   DETEKCE GPU
echo ============================================================

set "GPU_TYP=neznamy"

:: Zjistime typ GPU pomoci WMIC
for /f "tokens=*" %%i in ('wmic path win32_VideoController get name ^| findstr /i "NVIDIA"') do (
    set "GPU_TYP=NVIDIA"
    echo ✅ NVIDIA GPU detekovana!
    goto :gpu_nalezena
)

for /f "tokens=*" %%i in ('wmic path win32_VideoController get name ^| findstr /i "AMD"') do (
    set "GPU_TYP=AMD"
    echo ✅ AMD GPU detekovana!
    goto :gpu_nalezena
)

for /f "tokens=*" %%i in ('wmic path win32_VideoController get name ^| findstr /i "Intel"') do (
    set "GPU_TYP=Intel"
    echo ✅ Intel GPU detekovana!
    goto :gpu_nalezena
)

:gpu_nalezena

if "%GPU_TYP%"=="neznamy" (
    echo ❌ Nebyla detekovana zadna podporovana GPU.
    echo    Spoustim CPU verzi...
    timeout /t 2 /nobreak > nul
    start "" "spustit_cpu.bat"
    exit /b 0
)

:: ============================================================
::   NASTAVENI BACKENDU PODLE VYROBCE
:: ============================================================
echo.
echo ============================================================
echo   INSTALACE ZAVISLOSTI
echo ============================================================

:: Instalace zakladnich knihoven
echo Instaluji zakladni knihovny...
pip install flask flask-cors chromadb sentence-transformers google-generativeai requests torch transformers accelerate

if errorlevel 1 (
    echo CHYBA: Instalace zakladnich knihoven selhala!
    pause
    exit /b 1
)

:: ============================================================
::   INSTALACE LLAMA-CPP-PYTHON S PODPOROU GPU
:: ============================================================
echo.
echo ============================================================
echo   INSTALACE LLAMA-CPP-PYTHON
echo ============================================================

if "%GPU_TYP%"=="NVIDIA" (
    echo.
    echo NVIDIA GPU - instaluji CUDA verzi...
    echo To muze trvat 10-20 minut...
    echo.
    set "CMAKE_ARGS=-DGGML_CUDA=ON"
    pip install llama-cpp-python --force-reinstall --no-cache-dir
    
    if errorlevel 1 (
        echo.
        echo ❌ CUDA instalace selhala!
        echo Spoustim CPU verzi...
        timeout /t 2 /nobreak > nul
        start "" "spustit_cpu.bat"
        exit /b 0
    )
    echo ✅ CUDA verze nainstalovana!
)

if "%GPU_TYP%"=="AMD" (
    echo.
    echo AMD GPU - instaluji Vulkan verzi...
    echo To muze trvat 10-20 minut...
    echo.
    echo Poznamka: Pro AMD je Vulkan nejspolehlivejsi cesta.
    echo.
    set "CMAKE_ARGS=-DGGML_VULKAN=ON"
    pip install llama-cpp-python --force-reinstall --no-cache-dir
    
    if errorlevel 1 (
        echo.
        echo ❌ Vulkan instalace selhala!
        echo Zkousim CPU verzi...
        timeout /t 2 /nobreak > nul
        start "" "spustit_cpu.bat"
        exit /b 0
    )
    echo ✅ Vulkan verze nainstalovana!
)

if "%GPU_TYP%"=="Intel" (
    echo.
    echo Intel GPU - instaluji OpenVINO verzi...
    echo To muze trvat 10-20 minut...
    echo.
    echo POZOR: OpenVINO vyzaduje Intel oneAPI Toolkit!
    echo Pokud instalace selze, bude pouzita CPU verze.
    echo.
    set "CMAKE_ARGS=-DGGML_OPENVINO=ON"
    pip install llama-cpp-python --force-reinstall --no-cache-dir
    
    if errorlevel 1 (
        echo.
        echo ❌ OpenVINO instalace selhala!
        echo Zkousim CPU verzi...
        timeout /t 2 /nobreak > nul
        start "" "spustit_cpu.bat"
        exit /b 0
    )
    echo ✅ OpenVINO verze nainstalovana!
)

:: ============================================================
::   SPUSTENI SERVERU
:: ============================================================
echo.
echo ============================================================
echo   SPOUSTENI SERVERU
echo ============================================================
echo Spoustim server v novem okne...
start "MojeAI - Server (GPU)" cmd /k python app.py

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