@echo off
setlocal enabledelayedexpansion

:: ─────────────────────────────────────────────────────────────────────────────
::  Factorio Access Launcher - run without a compiled exe
::
::  First run: downloads uv and Python (if needed), installs dependencies,
::  then starts the launcher.
::  Subsequent runs: skips setup and starts immediately.
::
::  Requirements:
::    - Internet access (first run only)
::    - git (for the git+https://... playsound dependency and submodules)
:: ─────────────────────────────────────────────────────────────────────────────

set VENV_DIR=.venv
set UV_DIR=.uv
set SETUP_MARKER=.setup_done

:: Run from the script's own directory so all relative paths are correct.
cd /d "%~dp0"

echo ============================================================
echo  Factorio Access Launcher
echo ============================================================
echo.

:: ── Fast path: already set up ────────────────────────────────────────────────

if exist "%VENV_DIR%\Scripts\python.exe" if exist "%SETUP_MARKER%" goto :run

echo First-time setup - this only runs once.
echo.

:: ── Step 1: Ensure git submodules are populated ───────────────────────────────
:: ao2 and launcher-audio are submodules. If empty, pip install will fail.

git --version >nul 2>&1
if !errorlevel! neq 0 (
    echo WARNING: git not found on PATH.
    echo   - Submodule packages ^(ao2, launcher-audio^) may already be present.
    echo   - The playsound dependency requires git to install from GitHub.
    echo   If setup fails, install git from https://git-scm.com and re-run.
    echo.
) else (
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

:: ── Step 2: Download uv if not already present ───────────────────────────────

if not exist "%UV_DIR%\uv.exe" (
    set ARCH=x86_64
    if "!PROCESSOR_ARCHITECTURE!"=="ARM64" set ARCH=aarch64

    echo Downloading uv (!ARCH!)...
    curl --fail --location --progress-bar ^
        -o uv.zip ^
        "https://github.com/astral-sh/uv/releases/latest/download/uv-!ARCH!-pc-windows-msvc.zip"
    if !errorlevel! neq 0 (
        echo ERROR: Download failed. Check your internet connection.
        if exist uv.zip del uv.zip
        pause
        exit /b 1
    )

    powershell -NoProfile -Command ^
        "Expand-Archive -Path 'uv.zip' -DestinationPath '%UV_DIR%' -Force"
    del uv.zip
) else (
    echo Using existing uv.
)

:: ── Step 3: Create venv with Python 3.11 and install dependencies ─────────────

echo Setting up Python 3.11...
"%UV_DIR%\uv.exe" python install 3.11
if !errorlevel! neq 0 (
    echo ERROR: Could not install Python 3.11.
    pause
    exit /b 1
)

echo Creating virtual environment...
"%UV_DIR%\uv.exe" venv "%VENV_DIR%" --python 3.11
if !errorlevel! neq 0 (
    echo ERROR: Could not create virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies (this may take a minute)...
"%UV_DIR%\uv.exe" pip install -r requirements.txt --python "%VENV_DIR%\Scripts\python.exe"
if !errorlevel! neq 0 (
    echo.
    echo ERROR: Dependency install failed.
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
echo. > "%SETUP_MARKER%"

echo.
echo Setup complete.
echo.

:: ── Step 4: Run ───────────────────────────────────────────────────────────────

:run
"%VENV_DIR%\Scripts\python.exe" main.py %*
