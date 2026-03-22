@echo off
setlocal enabledelayedexpansion

:: ─────────────────────────────────────────────────────────────────────────────
::  Factorio Access Launcher - run without a compiled exe
::
::  First run: downloads Python (if needed), sets up the environment via
::  build_main.py --setup-only, then starts the launcher.
::  Subsequent runs: skips setup and starts immediately.
::
::  Requirements:
::    - Internet access (first run only)
::    - git (for the git+https://... playsound dependency and submodules)
::    - Microsoft C++ Build Tools (for the fa_launcher_audio C extension)
:: ─────────────────────────────────────────────────────────────────────────────

set VENV_DIR=venv
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

:: ── Step 2: Find or download Python ──────────────────────────────────────────

set BASE_PYTHON=

:: Look for Python 3.11+ on PATH
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set _SYS_VER=%%v
if defined _SYS_VER (
    for /f "tokens=1,2 delims=." %%a in ("!_SYS_VER!") do (
        if "%%a"=="3" if %%b GEQ 11 set BASE_PYTHON=python
    )
)

if not defined BASE_PYTHON (
    echo Python 3.11+ not found on PATH.

    if not exist "%UV_DIR%\uv.exe" (
        set ARCH=x86_64
        if "!PROCESSOR_ARCHITECTURE!"=="ARM64" set ARCH=aarch64

        echo Downloading uv ^(!ARCH!^)...
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
        if !errorlevel! neq 0 (
            echo ERROR: Failed to extract uv.zip.
            if exist uv.zip del uv.zip
            pause
            exit /b 1
        )
        del uv.zip
    )

    echo Installing Python 3.11 via uv...
    "%UV_DIR%\uv.exe" python install 3.11
    if !errorlevel! neq 0 (
        echo ERROR: Could not install Python 3.11.
        pause
        exit /b 1
    )

    :: Get the path to the uv-managed Python executable
    "%UV_DIR%\uv.exe" python find 3.11 > .python_path.tmp 2>&1
    set /p BASE_PYTHON=<.python_path.tmp
    del .python_path.tmp
) else (
    echo Found system Python !_SYS_VER!
)

:: ── Step 3: Set up environment via build_main.py ─────────────────────────────
:: build_main.py --setup-only creates ./venv and installs dependencies,
:: then exits before running PyInstaller.

echo Setting up environment...
"%BASE_PYTHON%" build_main.py --setup-only

:: Verify the venv was actually created, since build_main.py doesn't
:: propagate pip errors as a non-zero exit code.
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo.
    echo ERROR: Environment setup failed. Common causes:
    echo   - git not on PATH  ^(needed for the playsound GitHub dependency^)
    echo   - git submodules empty  ^(run: git submodule update --init^)
    echo   - no internet access
    echo.
    pause
    exit /b 1
)

:: Verify key packages installed correctly.
:: fa_launcher_audio requires Microsoft C++ Build Tools to compile its C extension.
:: playsound requires git to install from GitHub.
"%VENV_DIR%\Scripts\python.exe" -c "import fa_launcher_audio" >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo ERROR: Dependencies did not install correctly ^(fa_launcher_audio is missing^).
    echo This package requires Microsoft C++ Build Tools to compile.
    echo.
    echo Cleaning up so the next run retries setup...
    rmdir /s /q "%VENV_DIR%"
    echo.
    echo Please install Microsoft C++ Build Tools, then run this script again.
    echo Get them from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo ^(Install the "Desktop development with C++" workload^)
    echo.
    pause
    exit /b 1
)

"%VENV_DIR%\Scripts\python.exe" -c "import playsound" >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo ERROR: Dependencies did not install correctly ^(playsound is missing^).
    echo This usually means git was not on PATH during pip install.
    echo.
    echo Cleaning up so the next run retries setup...
    rmdir /s /q "%VENV_DIR%"
    echo.
    echo Please ensure git is installed and on PATH, then run this script again.
    echo Get git from https://git-scm.com
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
