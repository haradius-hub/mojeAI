@echo off
setlocal
cd /d "%~dp0"
title MojeAI - Portable Setup

set "PYTHON=python\python.exe"

echo ============================================================
echo    MOJEAI - PORTABLE SETUP
echo ============================================================
echo.

if not exist "%PYTHON%" goto :download_python

echo [INFO] Kontroluji Portable Python...
"%PYTHON%" -c "import socket, ssl, sqlite3, zlib" >nul 2>&1
if errorlevel 1 (
    echo [VAROVANI] Portable Python je nekompletni nebo poskozeny.
    echo [INFO] Obnovuji soubory z oficialni distribuce Pythonu...
    goto :download_python
)
goto :python_ready

:download_python
echo [1/4] Stahuji Embedded Python 3.12.3...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip' -OutFile 'python.zip'"
if errorlevel 1 goto :download_error
if not exist "python.zip" goto :download_error

echo [2/4] Rozbaluji nebo obnovuji Python...
if not exist "python" mkdir "python"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force"
if errorlevel 1 goto :extract_error
del "python.zip"

if not exist "%PYTHON%" goto :python_error
"%PYTHON%" -c "import socket, ssl, sqlite3, zlib" >nul 2>&1
if errorlevel 1 goto :python_error

:python_ready
if not exist "python\python312._pth" (
    echo [CHYBA] Soubor python\python312._pth nebyl nalezen.
    goto :error
)

echo [3/4] Povoleni site-packages...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $p='python\python312._pth'; $c=Get-Content $p; $c=$c -replace '^#import site$','import site'; Set-Content -Path $p -Value $c"
if errorlevel 1 goto :error

echo Cistim predchozi Python balicky...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $p='python\Lib\site-packages'; if (Test-Path $p) { Remove-Item -LiteralPath $p -Recurse -Force }; New-Item -ItemType Directory -Force -Path $p | Out-Null"
if errorlevel 1 goto :error

echo Stahuji get-pip.py...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
if errorlevel 1 goto :download_error
if not exist "get-pip.py" goto :download_error

echo Instaluji cisty pip...
"%PYTHON%" get-pip.py
if errorlevel 1 goto :error

"%PYTHON%" -m pip --version
if errorlevel 1 goto :error

echo.
echo [4/4] Instaluji zakladni zavislosti...
"%PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error

"%PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Instaluji CPU verzi llama-cpp-python...
"%PYTHON%" -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
if errorlevel 1 (
    echo [VAROVANI] llama-cpp-python se nepodarilo nainstalovat.
    echo Cloudove modely mohou fungovat, ale GGUF a semanticka pamet nebudou dostupne.
)

echo.
echo ============================================================
echo    PORTABLE PROSTREDI JE PRIPRAVENO
echo ============================================================
echo Spusteni: python\python.exe run.py
echo.
pause
exit /b 0

:download_error
echo [CHYBA] Stazeni souboru se nezdarilo. Zkontroluj pripojeni k internetu.
goto :error

:extract_error
echo [CHYBA] Rozbaleni Embedded Pythonu se nezdarilo.
if exist "python.zip" del "python.zip"
goto :error

:python_error
echo [CHYBA] Ani obnovena distribuce Pythonu neprosla kontrolou modulu.
echo Zkontroluj antivir a obsah slozky python.
goto :error

:error
echo.
echo [CHYBA] Instalace nebyla dokoncena. Zkontroluj hlaseni vyse.
if exist "python.zip" del "python.zip"
pause
exit /b 1
