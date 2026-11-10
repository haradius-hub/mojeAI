@echo off
title MojeAI - Portable Setup
setlocal enabledelayedexpansion

echo ============================================================
echo    MOJEAI - Portable Setup (Cesta B)
echo ============================================================
echo Tento skript nastavi plne prenosne prostredi.
echo Vse bude ulozeno ve slozce 'python' a 'Lib' v tomto adresari.
echo.

:: 1. Kontrola, zda uz Python neni stazeny
if exist "python\python.exe" (
    echo [INFO] Portable Python jiz existuje. Preskakuji stahovani.
    goto :install_deps
)

:: 2. Stazeni Embedded Python 3.12.3
echo [1/3] Stahuji Embedded Python 3.12.3...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip' -OutFile 'python.zip'"
if not exist "python.zip" (
    echo [CHYBA] Stazeni Pythonu selhalo. Zkontroluj pripojeni k internetu.
    pause
    exit /b 1
)

echo [2/3] Rozbaluji Python...
powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force"
del python.zip

:: 3. Uprava python312._pth pro povoleni site-packages
echo [3/3] Konfiguruji Python...
if exist "python\python312._pth" (
    powershell -Command "(Get-Content 'python\python312._pth') -replace '#import site', 'import site' | Set-Content 'python\python312._pth'"
)

:: 4. Stazeni get-pip.py
if not exist "get-pip.py" (
    echo Stahuji get-pip.py...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
)

echo Instaluji pip...
python\python.exe get-pip.py

:install_deps
:: 5. Instalace zavislosti
echo.
echo ============================================================
echo    INSTALACE ZAVISLOSTI
echo ============================================================
echo Instaluji setuptools a wheel...
python\python.exe -m pip install --upgrade setuptools wheel

echo Instaluji zakladni knihovny a sqlite-vec...
python\python.exe -m pip install -r requirements.txt

echo Instaluji llama-cpp-python (CPU verze)...
python\python.exe -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

echo.
echo ============================================================
echo    HOTOVO!
echo ============================================================
echo Prostredi je pripravene. Nyni muzes spustit aplikaci:
echo   python\python.exe run.py
echo.
pause
