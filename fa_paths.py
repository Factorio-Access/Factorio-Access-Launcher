import os
import sys
import re
import subprocess
import traceback
from pathlib import Path
from enum import StrEnum, auto
from fa_arg_parse import args, d_print, launch_args

__all__ = [
    "MOD_NAME",
    "BIN",
    "CONFIG",
    "READ_DIR",
    "WRITE_DIR",
    "MODS",
    "SAVES",
    "PLAYER_DATA",
    "SCRIPT_OUTPUT",
    "FACTORIO_VERSION" "find_bin",
    "find_config",
]


class PathNotInitialized(ValueError):
    pass


class PathNotFound(ValueError):
    pass


def get_path(name: str):
    ret = paths[name]
    if ret is None:
        raise PathNotInitialized(name)
    return ret


MOD_NAME = "FactorioAccess"


class d_printing_dict(dict):
    def __setitem__(self, key, value):
        d_print(f"{key}={value}")
        return super().__setitem__(key, value)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return None


paths: dict[str, Path | None] = d_printing_dict()

BIN = lambda: get_path("BIN")
CONFIG = lambda: get_path("CONFIG")
READ_DIR = lambda: get_path("READ_DIR")
WRITE_DIR = lambda: get_path("WRITE_DIR")
MODS = lambda: get_path("MODS")
SAVES = lambda: get_path("SAVES")
PLAYER_DATA = lambda: get_path("PLAYER_DATA")
SCRIPT_OUTPUT = lambda: get_path("SCRIPT_OUTPUT")

steam = False
steam_game = "427520"


class OS_flavor(StrEnum):
    MAC = "darwin"
    WIN = "win32"
    LIN = "linux"


class process:
    WRITE_DATA = {
        OS_flavor.MAC: "~/Library/Application Support/factorio",
        OS_flavor.WIN: R"%appdata%\Factorio",
        OS_flavor.LIN: "~/.factorio",
    }[sys.platform]
    WRITE_DATA = os.path.expandvars(WRITE_DATA)
    WRITE_DATA = os.path.expanduser(WRITE_DATA)
    read_data = paths["BIN"].parent
    if sys.platform != OS_flavor.MAC:
        read_data = read_data.parent
    read_data /= "data"
    factorio_replacements = {
        "__PATH__system-write-data__": WRITE_DATA,
        "__PATH__executable__": str(paths["BIN"].parent),
        "__PATH__system-read-data__": str(read_data),
    }

    def __new__(cls, p: str | Path):
        if isinstance(p, Path):
            p = str(p)
        for k, v in cls.factorio_replacements.items():
            p = p.replace(k, v)
        p = os.path.expanduser(p)
        p = os.path.expandvars(p)
        return Path(p).resolve()


def get_first_file(l: list[str | Path]):
    for p in l:
        path = process(p)
        if path.is_file():
            return path
        d_print(f"checked {p=} {path=}")
    raise PathNotFound()


def find_bin_without_steam_check():

    if args.executable_path:
        test = Path(args.executable_path)
        if test.is_file():
            paths["BIN"] = test
            return
        raise PathNotFound(
            "The path specified in the --executable-path argument does not exist"
        )
    if args.bin:
        _check_end = "factorio"
        if sys.platform == OS_flavor.WIN:
            _check_end += ".exe"
        for arg in launch_args:
            if arg.lower().endswith(_check_end):
                test = Path(arg)
                if test.is_file():
                    paths["BIN"] = test
                    return
        raise PathNotFound(
            "It looks like a command line option was given to launch factorio, but we couldn't figure out where factorio is located. Please add the --executable-path option with the location of the factorio binary to be launched"
        )

    from __main__ import __file__ as main_file

    if getattr(sys, "frozen", False):
        MY_BIN = sys.executable
    else:
        MY_BIN = main_file
    MY_CONFIG_DIR = Path(MY_BIN).parent

    exe_map = {
        OS_flavor.WIN: [
            "./bin/x64/factorio.exe",
            "../bin/x64/factorio.exe",
            MY_CONFIG_DIR / "./bin/x64/factorio.exe",
            MY_CONFIG_DIR / "../bin/x64/factorio.exe",
            R"%ProgramFiles%\Factorio\bin\x64\factorio.exe",
            R"%ProgramFiles(x86)%\Steam\steamapps\common\Factorio\bin\x64\factorio.exe",
        ],
        OS_flavor.MAC: [
            "/Applications/factorio.app/Contents/MacOS/factorio",
            "~/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio",
        ],
        OS_flavor.LIN: [
            "./bin/x64/factorio",
            "../bin/x64/factorio",
            MY_CONFIG_DIR / "./bin/x64/factorio.exe",
            MY_CONFIG_DIR / "../bin/x64/factorio.exe",
            "~/.steam/root/steam/steamapps/common/Factorio/bin/x64/factorio",
            "~/.steam/steam/steamapps/common/Factorio/bin/x64/factorio",
        ],
    }
    paths["BIN"] = get_first_file(exe_map[sys.platform])


inserted_bin_into_launch_args = False


def find_bin():
    global FACTORIO_VERSION
    global steam
    find_bin_without_steam_check()
    if "steam" in paths["BIN"].parts:
        steam = True
        if os.environ.get("SteamAppId", "") == steam_game:
            return
        if True:
            os.environ["SteamAppId"] = steam_game
        else:
            print(
                "Looks like you have a steam installed version of factorio, but didn't launch this launcher through steam. Please launch through steam after updating it's command line parameters to the following:"
            )
            print('"' + os.path.abspath(MY_BIN) + '" %command%')
            input("press enter to exit")
            raise SystemExit
    p_args = [paths["BIN"], "--version"]
    factorio_stdout = subprocess.check_output(p_args).decode()
    factorio_version_match = re.search(r"Version: (\d+\.\d+.\d+)", factorio_stdout)
    if not factorio_version_match:
        input(
            f"The executable found produced a strange version string. {BIN} {factorio_stdout}\n Press Enter to Exit"
        )
        raise SystemExit
    FACTORIO_VERSION = factorio_version_match[1]
    if inserted_bin_into_launch_args:
        launch_args[0] = str(paths["BIN"])
    else:
        launch_args.insert(0, str(paths["BIN"]))
        inserted_bin_into_launch_args = True


def find_config():
    import fa_menu
    from launch_and_monitor import launch_with_params

    if args.config:
        test = Path(args.config)
        if test.is_file():
            paths["CONFIG"] = test
            return
        print(f"could not find config file:{args.config}")
        input("press enter to exit...")
        raise SystemExit

    config_path = "config/config.ini"
    configs = []  # [MY_CONFIG_DIR / config_path]
    # try to append another config path from config-path.cfg
    try:
        fp = process("__PATH__executable__/../../config-path.cfg").open(encoding="utf8")
    except FileNotFoundError:
        configs.append(process("__PATH__system-write-data__") / config_path)
    else:
        with fp:
            for line in fp:
                match = re.match(r"config-path=(.*)", line)
                if match:
                    configs.append(process(match[1]) / "config.ini")
                    break
    try:
        config = get_first_file(configs)
    except PathNotFound:
        if not fa_menu.getAffirmation(
            "Unable to find the factorio config. Would you like to create a configuration in the default location?"
        ):
            raise SystemExit
        with configs[0].open(mode="w", encoding="utf8") as fp:
            pass
        launch_with_params(
            [], announce_press_e=True, save_rename=False, config_reset=True
        )
        try:
            config = get_first_file(configs)
        except PathNotFound:
            input(
                "Configuration creation failed. Please report to Factorio Access Maintainers\nPress Enter to exit."
            )
            raise SystemExit

    if "-c" in launch_args:
        launch_args[launch_args.index("-c") + 1] = str(config)
    else:
        launch_args.append("-c")
        launch_args.append(str(config))
    d_print(f"{config}")
    paths["CONFIG"] = config


def read_write_dirs(config: Path):
    write: Path | None = None
    read: Path | None = None
    find_write = re.compile(r"write-data=(.*)")
    find_read = re.compile(r"read-data=(.*)")
    with config.open(encoding="utf8") as fp:
        for line in fp:
            if match := find_write.match(line):
                write = process(match[1])
                if not write.is_dir():
                    raise Exception(f'Write directory "{write}" is not a directory.')
            if match := find_read.match(line):
                read = process(match[1])
                if not read.is_dir():
                    raise Exception(f'Read directory "{read}" is not a directory.')
            if write and read:
                paths["WRITE_DIR"] = write
                paths["READ_DIR"] = read
                d_print(f"{write=}\n{read=}")
    raise Exception("Unable to find path directives in config file:{config}")


def find_mod_folder():
    if args.mod_directory:
        mods = Path(args.mod_directory)
    else:
        mods = paths["WRITE_DIR"] / "mods"
    if not mods.is_dir():
        if mods.is_file():
            print("Mod Directory cannot be a file.")
            input("Press Enter to exit...")
            raise SystemExit
        import fa_menu

        print(f"The mod folder {mods} does not exist. Would you like to create it?")
        if not fa_menu.getAffirmation():
            raise SystemExit
        mods.mkdir()
    paths["MODS"] = mods
    d_print(f"{mods=}")


def find_everything_else():
    paths["SAVES"] = paths["WRITE_DIR"] / "saves"

    player_data_folder = paths["WRITE_DIR"]
    if steam:
        player_data_folder = get_steam_player_data_folder()

    paths["PLAYER_DATA"] = player_data_folder / "player-data.json"
    paths["TEMP"] = paths["WRITE_DIR"] / "temp"
    paths["SCRIPT_OUTPUT"] = paths["WRITE_DIR"] / "script-output"


def get_steam_player_data_folder():
    _user = os.environ["SteamAppUser"]
    steam_game_path = Path(os.getcwd())
    steam_path = steam_game_path.joinpath("..", "..", "..")
    if sys.platform == OS_flavor.WIN:
        import winreg

        _key = R"SOFTWARE\WOW6432Node\Valve\Steam"
        try:
            _hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _key)
            _install_path, _ = winreg.QueryValueEx(_hkey, "InstallPath")
            steam_path = Path(_install_path)
            d_print("steam path updated")
        except:
            traceback.print_exc()
    _steam_config = steam_path.joinpath("config", "config.vdf")
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
    steam_write_folder = steam_path.joinpath(
        "userdata", _account_id, steam_game, "remote"
    )
    steam_write_folder = steam_write_folder.resolve()
    d_print(steam_write_folder)
