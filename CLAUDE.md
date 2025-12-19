# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Factorio Access Launcher is a Python accessibility wrapper for Factorio. It provides text-based menus, screen reader integration via `accessible_output2`, and audio feedback to make Factorio playable for blind and visually impaired users.

## Commands

**Setup and Build:**
```bash
python build_main.py              # Creates venv, installs deps, builds dist/launcher.exe
python build_main.py --gui        # Build GUI version (no console window)
```

**Run:**
```bash
python main.py                    # Start the launcher
```

**Tests:**
```bash
python -m unittest discover       # Run all tests (discovers tests/test_*.py)
```

## Architecture

### Entry Points
- `main.py` - Interactive menu-driven launcher
- `build_main.py` - PyInstaller build wrapper

### Core Modules

**Menu System (`fa_menu.py`)** - Custom accessible menu framework with localization support. Base classes `MenuBase`, `Menu` handle keyboard input and screen reader output.

**Path Management (`fa_paths.py`)** - Auto-detects Factorio installation (Steam, MSI, zip). Exports global getters: `BIN`, `CONFIG`, `MODS`, `WRITE_DIR` and others.

**Configuration (`config.py`)** - INI file editor using `Conf_Editor` context manager. Handles both commented and active settings with regex-based lookup.

**Game Launch (`launch_and_monitor.py`)** - Subprocess management for Factorio. Monitors stdout in real-time for error detection, player events, and audio notifications.

**Mod Management (`mods.py`)** - Mod dependency resolution, Mod Portal API integration, version parsing, and download management. Uses TypedDict types: `ModInfoJson`, `Release`, `PortalResult`.

**Translations (`translations.py`)** - Extracts game prototype data, strips Factorio rich text markup, handles translation lookups with fallback chains.

**Multiplayer (`multiplayer.py`)** - Game list retrieval, friend management, hosting/joining via multiplayer.factorio.com API.

### Key Patterns

- **Localization First** - All UI strings use translation keys, never hardcoded
- **Context Managers** - Used for config editing and file operations
- **Recursive Menus** - Menus contain sub-menus with dynamic content
- **TypedDict** - Used for complex structures (mods, releases, portal results)
- **Module-level Constants** - Global paths set up at import time in `fa_paths.py`

### External Dependencies

Custom forks are used for screen reader and audio support:
- `accessible_output2` - Screen reader integration (Factorio-Access fork)
- `playsound` - Audio playback (killjoy1221 fork)
- `fa_launcher_audio` - Custom audio management module

## Platform Support

Primary target is Windows with PyInstaller. Linux and macOS have secondary support. Platform detection via `sys.platform`.

## Version Management

Uses git tags for semantic versioning. `version.py` extracts version info dynamically from git (tag, commits since tag, dirty state).
