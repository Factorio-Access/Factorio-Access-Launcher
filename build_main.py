import os
import sys
import shutil
from pathlib import Path

linux_hidden_modules = [
    "espeak",  # cspell:disable-line
    "python_espeak-0.5.egg-info",  # cspell:disable-line
    "speechd_config",  # cspell:disable-line
    "speechd",  # cspell:disable-line
]

if sys.base_prefix == sys.prefix:  # not in venv
    # raise ValueError("Must be run from venv.. Will fix to auto venv soon")

    venv = Path(".", "venv")

    if sys.platform == "win32":
        venv_python = venv.joinpath("Scripts", "python.exe")
    else:
        venv_python = venv.joinpath("bin", "python3")

    if not venv.is_dir():
        cmd = f'"{sys.executable}" -m venv {venv}'
        os.system(cmd)
        # cspell:disable-next-line
        cmd = f"{venv_python} -m pip install -r requirements.txt pyinstaller"
        os.system(cmd)
        if sys.platform == "linux":
            import site

            system_packages = site.getsitepackages()
            full_paths = []
            for mod in linux_hidden_modules:
                for base in system_packages:
                    test = Path(base).joinpath(mod)
                    if test.exists():
                        full_paths.append(str(test))

            copy_cmd = (
                "cp -r "
                + " ".join(full_paths)
                + " "
                + str(venv)
                + "/lib/python3.*/site-packages/"
            )
            print(copy_cmd)
            if os.system(copy_cmd):
                raise RuntimeError()
    cmd = f"{venv_python} {__file__}"
    os.system(cmd)
    raise SystemExit()

import PyInstaller.__main__

hidden_imports = []
if sys.platform == "linux":
    hidden_imports += linux_hidden_modules


locale_copy_error = None
try:
    p = Path("./mods/FactorioAccess/locale")
    base = Path("./r/locale")
    if not base.is_dir():
        raise Exception("missing resource locale folder")
    for loc in p.iterdir():
        file_to_copy = loc.joinpath("launcher.cfg")
        if not file_to_copy.is_file():
            continue
        dest = base.joinpath(loc.name + ".cfg")
        shutil.copyfile(file_to_copy, dest)
except Exception as e:
    locale_copy_error = e

do_gui = "--gui" in sys.argv

name = "launcher"

if do_gui:
    name += "_no_console"

spec = Path(name + ".spec")

if spec.is_file():
    args = [str(spec)]
    # os.system(venv_python + " -m PyInstaller launcher.spec")
else:
    args = [
        "--onefile",  # cspell:disable-line
        "main.py",
        "-n",
        name,
        "--add-data=./r:./r",
    ]
    if do_gui:
        args.append("--noconsole")  # cspell:disable-line
    for imp in hidden_imports:
        args.append("--hidden-import=" + imp)
    excludes = "FixTk tcl tk _tkinter tkinter Tkinter PIL".split(" ")
    for m in excludes:
        args.append("--exclude-module")
        args.append(m)
PyInstaller.__main__.run(args)

if locale_copy_error:
    print(locale_copy_error)
    print("warn: no locale files. If you're not developing. This is fine to ignore.")
