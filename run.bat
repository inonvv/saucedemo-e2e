@echo off
rem Double-click this file on Windows: it installs everything and runs the tests.
cd /d "%~dp0"

rem Find a working Python. The plain "python" name can be an empty Microsoft Store shortcut, so test it for real.
set "PY="
python -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    echo.
    echo Python is not installed on this computer. The tests need it.
    echo.
    echo Install it in one of two ways, then double-click run.bat again:
    echo   1. Download from https://www.python.org/downloads/ and tick "Add python.exe to PATH" in the installer.
    echo   2. Or paste this line in a terminal:  winget install -e --id Python.Python.3.13
    echo.
    echo No install wanted? The folder "evidence" holds a screenshot and the output of a finished run.
    echo.
    pause
    exit /b 1
)

echo [1/4] Creating the virtual environment...
if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv
if not exist ".venv\Scripts\python.exe" (
    echo Could not create the virtual environment.
    pause
    exit /b 1
)

echo [2/4] Installing packages...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo Package install failed. Check the internet connection.
    pause
    exit /b 1
)

echo [3/4] Installing the Chromium browser...
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 (
    echo Browser install failed. Check the internet connection.
    pause
    exit /b 1
)

echo [4/4] Running the tests...
".venv\Scripts\python.exe" -m pytest %*
echo.
echo Done. The line above with "passed" shows the result, for example "29 passed".

rem Show the Allure report: build a fresh one if the Allure tool is installed, else open the saved one.
set "REPORT="
where allure >nul 2>&1
if not errorlevel 1 (
    echo Building the Allure report of this run...
    call allure generate allure-results -o allure-report --clean --single-file >nul 2>&1
    if exist "allure-report\index.html" set "REPORT=allure-report\index.html"
)
if not defined REPORT if exist "evidence\allure-report\index.html" (
    echo The Allure tool is not installed here, so this opens the saved report of the author's run.
    set "REPORT=evidence\allure-report\index.html"
)
if defined REPORT (
    echo Opening the report in the browser: %REPORT%
    start "" "%REPORT%"
)
pause
