import os
import sys
import subprocess
from pathlib import Path

if sys.base_prefix == sys.prefix and "GITHUB_RUN_ID" not in os.environ:  # not in venv
    venv = Path(".", "venv")
    venv_python = venv.joinpath("Scripts", "python.exe")

    if not venv.is_dir():
        cmd = f'"{sys.executable}" -m venv {venv}'
        os.system(cmd)
        cmd = f"{venv_python} -m pip install -r requirements.txt nuitka"
        os.system(cmd)

    cmd = f"{venv_python} {__file__}"
    for arg in sys.argv[1:]:
        cmd += f" {arg}"
    os.system(cmd)
    raise SystemExit()

from version_freeze import frozen
from version import version

do_gui = "--gui" in sys.argv

# accessible_output2 submodule lib directory containing DLLs
ao2_lib = Path("ao2", "accessible_output2", "lib")

name = "launcher"
if do_gui:
    name += "_no_console"

# Parse version tag into tuple
ver_parts = version.tag.split(".")
# Pad to 4 parts for Windows version format
while len(ver_parts) < 4:
    ver_parts.append("0")
ver_str = ".".join(ver_parts[:4])

args = [
    sys.executable,
    "-m",
    "nuitka",
    "--onefile",
    f"--output-filename={name}.exe",
    "--output-dir=dist",
    # Data files
    "--include-data-dir=./r=./r",
    # accessible_output2 DLLs (--include-data-dir filters out DLLs, so use --include-data-files)
    f"--include-data-files={ao2_lib}/*.dll=accessible_output2/lib/",
    # Required modules
    "--include-module=_cffi_backend",
    "--include-package=fa_launcher_audio",
    "--include-package=accessible_output2",
    "--include-package=playsound",
    "--include-package=pyautogui",
    "--include-package=pyperclip",
    # Exclude unnecessary modules
    "--nofollow-import-to=tkinter",
    "--nofollow-import-to=_tkinter",
    "--nofollow-import-to=PIL",
    "--nofollow-import-to=FixTk",
    # Windows metadata
    f"--windows-company-name=Factorio Access",
    f"--windows-product-name=Factorio Access Launcher",
    f"--windows-file-version={ver_str}",
    f"--windows-product-version={ver_str}",
    f"--windows-file-description=Factorio Access Launcher",
    # Use MSVC
    "--msvc=latest",
    # Non-interactive (auto-download dependencies like Dependency Walker)
    "--assume-yes-for-downloads",
    # Show progress
    "--show-progress",
    "--show-memory",
]

if do_gui:
    args.append("--disable-console")

# Entry point
args.append("main.py")

print("Running Nuitka with args:")
for arg in args:
    print(f"  {arg}")
print()

with frozen():
    result = subprocess.run(args)
    sys.exit(result.returncode)
