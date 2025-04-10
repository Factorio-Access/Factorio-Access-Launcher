import os
import sys
import re
import subprocess
import traceback
from pathlib import Path

from __main__ import __file__ as main_file
from fa_arg_parse import args, d_print, launch_args


if getattr(sys, "frozen", False):
    MY_BIN = sys.executable
else:
    MY_BIN = main_file

MY_CONFIG_DIR = Path(MY_BIN).parent

MAC = "darwin"
WIN = "win32"
LIN = "linux"

WRITE_DATA_MAP = {
    MAC: "~/Library/Application Support/factorio",
    WIN: R"%appdata%\Factorio",
    LIN: "~/.factorio",
}

steam = "SteamClientLaunch" in os.environ
d_print(f"steam={steam}")

if steam:
    _user = os.environ["SteamAppUser"]
    _game = os.environ["SteamAppId"]
    steam_game_path = Path(os.getcwd())
    _steam_path = steam_game_path.joinpath("..", "..", "..")
    if sys.platform == WIN:
        import winreg

        _key = R"SOFTWARE\WOW6432Node\Valve\Steam"
        try:
            _hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _key)
            _install_path, _ = winreg.QueryValueEx(_hkey, "InstallPath")
            _steam_path = Path(_install_path)
            d_print("steam path updated")
        except:
            traceback.print_exc()
    _steam_config = _steam_path.joinpath("config", "config.vdf")
    with open(_steam_config, encoding="utf8") as fp:
        for _line in fp:
            if _user in _line:
                break
        _pat = re.compile(r'\s*"?SteamID"?\s+"?(\d+)')
        for _line in fp:
            if m := _pat.match(_line):
                _steam_id = m[1]
                break
        else:
            raise ValueError(
                "Unable to find SteamID. Please report this error to Factorio Access Launcher maintainer via discord issues channel."
            )
    _account_id = str(((1 << 32) - 1) & int(_steam_id))
    steam_write_folder = _steam_path.joinpath("userdata", _account_id, _game, "remote")
    steam_write_folder = steam_write_folder.absolute()
    d_print(steam_write_folder)

_check_end = "factorio"
if sys.platform == WIN:
    _check_end += ".exe"

BIN = MY_CONFIG_DIR.joinpath(_check_end)
if not BIN.is_file():
    BIN = None
    if args.bin:
        for arg in launch_args:
            if arg.lower().endswith(_check_end):
                if os.path.isfile(arg):
                    BIN = arg
                    break
        if not BIN:
            print(
                "It looks like a command line option was given to launch factorio, but we couldn't figure out where factorio is located. Please add the --executable-path option with the location of the factorio binary to be launched"
            )
            input("press enter to exit...")
            raise SystemExit
    else:
        exe_map = {
            WIN: [
                "./bin/x64/factorio.exe",
                R"%ProgramFiles%\Factorio\bin\x64\factorio.exe",
                R"%ProgramFiles(x86)%\Steam\steamapps\common\Factorio\bin\x64\factorio.exe",
            ],
            MAC: [
                "/Applications/factorio.app/Contents/MacOS/factorio",
                "~/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio",
            ],
            LIN: [
                "./bin/x64/factorio",
                "~/.steam/root/steam/steamapps/common/Factorio/bin/x64/factorio",
                "~/.steam/steam/steamapps/common/Factorio/bin/x64/factorio",
            ],
        }
        for path in exe_map[sys.platform]:
            path = os.path.expanduser(os.path.expandvars(path))
            if os.path.isfile(path):
                BIN = os.path.abspath(path)
                break
            d_print(f"checked:{path}")
        else:
            input(
                "Could not find factorio. If you've installed factorio in a standard way please contact the mod developers with your system details. If you're using the portable version please either place this launcher in the folder with the data and bin folders or launch with the factorio executable path as an argument."
            )
            raise SystemExit
    if str(BIN).find("steam") >= 0 and not steam:
        print(
            "Looks like you have a steam installed version of factorio, but didn't launch this launcher through steam. Please launch through steam after updating it's command line parameters to the following:"
        )
        print('"' + os.path.abspath(MY_BIN) + '" %command%')
        input("press enter to exit")
        raise SystemExit
launch_args.insert(0, BIN)

_FACTORIO_VER_out = subprocess.check_output([BIN, "--version"]).decode()
_factorio_version_match = re.search(r"Version: (\d+\.\d+.\d+)", _FACTORIO_VER_out)
if not _factorio_version_match:
    input(
        f"The executable found produced a strange version string. {BIN} {_FACTORIO_VER_out}\n Press Enter to Exit"
    )
    raise SystemExit
FACTORIO_VERSION = _factorio_version_match[1]


factorio_replacements = {
    "__PATH__system-write-data__": os.path.expanduser(
        os.path.expandvars(WRITE_DATA_MAP[sys.platform])
    ),
    "__PATH__executable__": os.path.dirname(BIN),
    "__PATH__system-read-data__": os.path.join(
        os.path.dirname(BIN), "..", "..", "data"
    ),
}
if sys.platform == MAC:
    factorio_replacements["__PATH__system-read-data__"] = os.path.join(
        os.path.dirname(BIN), "..", "data"
    )


def process(path):
    for k, v in factorio_replacements.items():
        path = path.replace(k, v)
    path = os.path.abspath(path)
    return path


if args.config:
    try:
        fp = open(args.config)
    except FileNotFoundError:
        print(f"could not find config file:{args.config}")
        input("press enter to exit...")
        raise SystemExit
    CONFIG = args.config
else:

    config_path = "config/config.ini"
    configs = [MY_CONFIG_DIR.joinpath(config_path)]
    # try to append another config path from config-path.cfg
    try:
        fp = open(
            process("__PATH__executable__/../../config-path.cfg"), encoding="utf8"
        )
    except FileNotFoundError:
        configs.append(
            process(os.path.join("__PATH__system-write-data__", config_path))
        )
    else:
        with fp:
            for line in fp:
                match = re.match(r"config-path=(.*)", line)
                if match:
                    configs.append(os.path.join(process(match.group(1)), "config.ini"))
                    break

    CONFIG = None

    def get_config():
        for path in configs:
            if os.path.isfile(path):
                return path

    CONFIG = get_config()
    if not CONFIG:
        import fa_menu

        print(
            "Unable to find the factorio config. Would you like to create a configuration in the default location?"
        )
        if not fa_menu.getAffirmation():
            raise SystemExit
        f_args = [BIN, "--start-server-load-scenario", "Fake"]
        subprocess.run(f_args, stdout=subprocess.DEVNULL)
        CONFIG = get_config()
        if not CONFIG:
            input(
                "Configuration creation failed. Please report to Factorio Access Maintainers\nPress Enter to exit."
            )
            raise SystemExit
    launch_args.append("-c")
    launch_args.append(CONFIG)
d_print(f"CONFIG={CONFIG}")
WRITE_DIR: Path | None = None
READ_DIR: Path | None = None
with open(CONFIG, encoding="utf8") as fp:
    for line in fp:
        if match := re.match(r"write-data=(.*)", line):
            WRITE_DIR = Path(process(match[1]))
        if match := re.match(r"read-data=(.*)", line):
            READ_DIR = Path(process(match[1]))
        if WRITE_DIR and READ_DIR:
            break
if not WRITE_DIR or not WRITE_DIR.is_dir():
    d_print(f"bad write dir:[{WRITE_DIR}]")
    raise Exception("Unable to find factorio write directory")
d_print(f"WRITE_DIR={WRITE_DIR}")
if not READ_DIR or not READ_DIR.is_dir():
    d_print(f"bad read dir:[{READ_DIR}]")
    raise Exception("Unable to find factorio data directory")
d_print(f"READ_DIR={READ_DIR}")


if args.mod_directory:
    MODS = Path(args.mod_directory)
else:
    MODS = WRITE_DIR.joinpath("mods")
if not MODS.is_dir():
    if MODS.is_file():
        print("Mod Directory cannot be a file.")
        input("Press Enter to exit...")
        raise SystemExit
    print(f"The mod folder {MODS} does not exist. Would you like to create it?")
    if not fa_menu.getAffirmation():
        raise SystemExit
    os.mkdir(MODS)
d_print(f"MODS={MODS}")

SAVES = WRITE_DIR.joinpath("saves")
d_print(f"SAVES={SAVES}")


PLAYER_DATA = (steam_write_folder if steam else WRITE_DIR).joinpath("player-data.json")
d_print(f"PLAYER_DATA={PLAYER_DATA}")


TEMP = WRITE_DIR.joinpath("temp")
d_print(f"TEMP={TEMP}")

SCRIPT_OUTPUT = WRITE_DIR.joinpath("script-output")
d_print(f"SCRIPT_OUTPUT={SCRIPT_OUTPUT}")

MOD_NAME = "FactorioAccess"
# __my_mod_folder = os.path.join(MY_BIN,'..','mods')
# if os.path.isdir(__my_mod_folder) and not os.path.samefile(__my_mod_folder,MODS):
#     __my_mod = os.path.join(__my_mod_folder,MOD_NAME)
#     if os.path.exists(__my_mod):
#         try:
#             shutil.rmtree(os.path.join(MODS,MOD_NAME))
#         except FileNotFoundError:
#             pass
#         shutil.move(__my_mod,MODS)
