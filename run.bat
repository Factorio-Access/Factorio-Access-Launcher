@echo off
setlocal enabledelayedexpansion

:: ─────────────────────────────────────────────────────────────────────────────
::  Factorio Access Launcher - run without a compiled exe
::
::  First run: downloads Python (if needed), installs dependencies, then starts.
::  Subsequent runs: skips setup and starts immediately.
::
::  Requirements:
::    - Internet access (first run only)
::    - git (for the git+https://... playsound dependency and submodules)
:: ─────────────────────────────────────────────────────────────────────────────

set PYTHON_VER=3.11.9
set EMBED_DIR=.python
set VENV_DIR=.venv
set SETUP_MARKER=.setup_done

:: Run from the script's own directory so all relative paths are correct.
cd /d "%~dp0"

echo ============================================================
echo  Factorio Access Launcher
echo ============================================================
echo.

:: ── Fast path: already set up ────────────────────────────────────────────────

if exist "%VENV_DIR%\Scripts\python.exe" goto :run
if exist "%EMBED_DIR%\python.exe" if exist "%SETUP_MARKER%" goto :run

echo First-time setup - this only runs once.
echo.

:: ── Step 1: Ensure git submodules are populated ───────────────────────────────
:: ao2 and launcher-audio are submodules. If empty, pip install will fail.

git --version >nul 2>&1
if !errorlevel! neq 0 (
    echo WARNING: git not found on PATH.
    echo   - Submodule packages (ao2, launcher-audio) may already be present.
    echo   - The playsound dependency requires git to install from GitHub.
    echo   If setup fails, install git from https://git-scm.com and re-run.
    echo.
) else (
    :: Check if ao2 looks empty (no setup.py / pyproject.toml)
    if not exist "ao2\setup.py" if not exist "ao2\pyproject.toml" (
        echo Initialising git submodules...
        git submodule update --init
        if !errorlevel! neq 0 (
            echo ERROR: git submodule update failed.
            pause
            exit /b 1
        )
    )
)

:: ── Step 2: Find or download Python ──────────────────────────────────────────

set BASE_PYTHON=
set USE_EMBED=0

:: Look for Python 3.11+ on PATH
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set _SYS_VER=%%v
if defined _SYS_VER (
    for /f "tokens=1,2 delims=." %%a in ("!_SYS_VER!") do (
        if "%%a"=="3" (
            if %%b GEQ 11 (
                set BASE_PYTHON=python
                echo Found system Python !_SYS_VER!
            )
        )
    )
)

if not defined BASE_PYTHON (
    set USE_EMBED=1

    if not exist "%EMBED_DIR%\python.exe" (
        echo Python 3.11+ not found on PATH.
        echo Downloading Python %PYTHON_VER% embeddable package...
        echo.

        curl --fail --location --progress-bar ^
            -o python-embed.zip ^
            "https://www.python.org/ftp/python/%PYTHON_VER%/python-%PYTHON_VER%-embed-amd64.zip"
        if !errorlevel! neq 0 (
            echo ERROR: Download failed. Check your internet connection.
            if exist python-embed.zip del python-embed.zip
            pause
            exit /b 1
        )

        echo Extracting...
        powershell -NoProfile -Command ^
            "Expand-Archive -Path 'python-embed.zip' -DestinationPath '%EMBED_DIR%' -Force"
        del python-embed.zip

        :: Enable site-packages in the embeddable distribution.
        :: The .pth file ships with 'import site' commented out.
        powershell -NoProfile -Command ^
            "(Get-Content '%EMBED_DIR%\python311._pth') -replace '#import site','import site' | Set-Content '%EMBED_DIR%\python311._pth'"

        :: Bootstrap pip (not included in the embeddable package)
        echo Bootstrapping pip...
        curl --fail --location --silent ^
            -o get-pip.py ^
            "https://bootstrap.pypa.io/get-pip.py"
        if !errorlevel! neq 0 (
            echo ERROR: Could not download get-pip.py.
            pause
            exit /b 1
        )
        "%EMBED_DIR%\python.exe" get-pip.py --no-warn-script-location -q
        del get-pip.py
    ) else (
        echo Using existing embedded Python.
    )

    set BASE_PYTHON=%EMBED_DIR%\python.exe
)

:: ── Step 3: Create venv (system Python only) or use embed directly ───────────

if %USE_EMBED%==0 (
    if not exist "%VENV_DIR%\Scripts\python.exe" (
        echo Creating virtual environment...
        %BASE_PYTHON% -m venv %VENV_DIR%
        if !errorlevel! neq 0 (
            echo ERROR: Could not create virtual environment.
            pause
            exit /b 1
        )
    )
    set RUN_PYTHON=%VENV_DIR%\Scripts\python.exe
) else (
    :: Embeddable Python is already self-contained; no separate venv needed.
    set RUN_PYTHON=%EMBED_DIR%\python.exe
)

:: ── Step 4: Install dependencies ─────────────────────────────────────────────

echo Installing dependencies (this may take a minute)...
echo.

"%RUN_PYTHON%" -m pip install --upgrade pip -q
"%RUN_PYTHON%" -m pip install -r requirements.txt

if !errorlevel! neq 0 (
    echo.
    echo ERROR: pip install failed.
    echo.
    echo Common causes:
    echo   - git not on PATH  ^(needed for the playsound GitHub dependency^)
    echo   - git submodules empty  ^(run: git submodule update --init^)
    echo   - no internet access
    echo.
    pause
    exit /b 1
)

:: Mark setup as complete so we skip all of this next time.
echo. > %SETUP_MARKER%

echo.
echo Setup complete.
echo.

:: ── Step 5: Run ───────────────────────────────────────────────────────────────

:run
if exist "%VENV_DIR%\Scripts\python.exe" (
    set RUN_PYTHON=%VENV_DIR%\Scripts\python.exe
) else (
    set RUN_PYTHON=%EMBED_DIR%\python.exe
)

"%RUN_PYTHON%" main.py %*
