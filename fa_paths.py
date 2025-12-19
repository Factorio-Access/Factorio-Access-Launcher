import os
import sys
import re
import subprocess
import traceback
from pathlib import Path
from enum import StrEnum, auto
from typing import Callable

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
    "TEMP",
    "FACTORIO_VERSION",
]


class PathNotInitialized(ValueError):
    pass


class PathNotFound(ValueError):
    pass


def get_path(name: str, find_func: Callable, force: bool = False) -> Path:
    if not force and name in paths:
        return paths[name]
    find_func()
    if name in paths:
        return paths[name]
    raise PathNotInitialized(name)


MOD_NAME = "FactorioAccess"


paths: dict[str, Path] = {}

BIN = lambda force=False: get_path("BIN", find_bin, force)
CONFIG = lambda force=False: get_path("CONFIG", find_config, force)
READ_DIR = lambda force=False: get_path("READ_DIR", find_read_write_dirs, force)
WRITE_DIR = lambda force=False: get_path("WRITE_DIR", find_read_write_dirs, force)
MODS = lambda force=False: get_path("MODS", find_mod_folder, force)
SAVES = lambda force=False: get_path("SAVES", find_everything_else, force)
PLAYER_DATA = lambda force=False: get_path("PLAYER_DATA", find_everything_else, force)
SCRIPT_OUTPUT = lambda force=False: get_path(
    "SCRIPT_OUTPUT", find_everything_else, force
)
TEMP = lambda force=False: get_path("TEMP", find_everything_else, force)
FACTORIO_VERSION = lambda force=False: factorio_ver

steam = False
steam_game = "427520"


class OS_flavor(StrEnum):
    MAC = "darwin"
    WIN = "win32"
    LIN = "linux"


class process:
    sys_write = {
        OS_flavor.MAC: "~/Library/Application Support/factorio",
        OS_flavor.WIN: R"%appdata%\Factorio",
        OS_flavor.LIN: "~/.factorio",
    }[OS_flavor(sys.platform)]
    sys_write = os.path.expandvars(sys_write)
    sys_write = os.path.expanduser(sys_write)

    @staticmethod
    def exe():
        return str(BIN())

    @staticmethod
    def read():
        read_data = BIN().parent
        if sys.platform != OS_flavor.MAC:
            read_data = read_data.parent
        read_data /= "data"
        return str(read_data)

    factorio_replacements = {
        "__PATH__system-write-data__": lambda: process.sys_write,
        "__PATH__executable__": exe,
        "__PATH__system-read-data__": read,
    }

    def __new__(cls, p: str | Path):
        if isinstance(p, Path):
            p = str(p)
        for k, v in cls.factorio_replacements.items():
            if k in p:
                p = p.replace(k, v())
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
    if getattr(sys, "frozen", False):
        MY_BIN = sys.executable
    else:
        from __main__ import __file__ as MY_BIN
    MY_CONFIG_DIR = Path(MY_BIN).parent

    if args.executable_path:
        test = Path(args.executable_path)
        if test.is_file():
            paths["BIN"] = test
            return MY_BIN
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
                    return MY_BIN
        raise PathNotFound(
            "It looks like a command line option was given to launch factorio, but we couldn't figure out where factorio is located. Please add the --executable-path option with the location of the factorio binary to be launched"
        )

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
    paths["BIN"] = get_first_file(exe_map[OS_flavor(sys.platform)])
    return MY_BIN


def steam_check(MY_BIN: str):
    global steam
    if "steam" not in paths["BIN"].parts:
        return
    steam = True
    if os.environ.get("SteamAppId", "") == steam_game:
        return
    if False:
        os.environ["SteamAppId"] = steam_game
        # need to get user ID too for player data file location :(
    else:
        print(
            "Looks like you have a steam installed version of factorio, but didn't launch this launcher through steam. Please launch through steam after updating it's command line parameters to the following:"
        )
        print(f'"{MY_BIN}" %command%')
        input("press enter to exit")
        raise SystemExit


inserted_bin_into_launch_args = False


def find_bin(force=False):
    global factorio_ver
    global steam
    global inserted_bin_into_launch_args
    force  # type: ignore
    my_bin = find_bin_without_steam_check()
    steam_check(my_bin)
    p_args = [paths["BIN"], "--version"]
    factorio_stdout = subprocess.check_output(p_args).decode()
    factorio_version_match = re.search(r"Version: (\d+\.\d+.\d+)", factorio_stdout)
    if not factorio_version_match:
        input(
            f"The executable found produced a strange version string. {BIN} {factorio_stdout}\n Press Enter to Exit"
        )
        raise SystemExit
    factorio_ver = factorio_version_match[1]
    if inserted_bin_into_launch_args:
        launch_args[0] = str(paths["BIN"])
    else:
        launch_args.insert(0, str(paths["BIN"]))
        inserted_bin_into_launch_args = True


def find_config(force=False):
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
        bin = BIN(force)
        if factorio_ver == "2.0.72":
            configs[0].parent.mkdir(parents=True, exist_ok=True)
            with configs[0].open(mode="w", encoding="utf8") as fp:
                pass
            launch_with_params(
                [], announce_press_e=True, save_rename=False, config_reset=True
            )
        else:
            subprocess.run([bin, "--start-server-load-scenario", "fake"])
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


def find_read_write_dirs(force=False):
    write: Path | None = None
    read: Path | None = None
    find_write = re.compile(r"write-data=(.*)")
    find_read = re.compile(r"read-data=(.*)")
    config = CONFIG(force)
    with config.open(encoding="utf8") as fp:
        for line in fp:
            if match := find_write.match(line):
                write = process(match[1])
                if not write.is_dir():
                    raise PathNotFound(
                        f'Write directory "{write}" in config {config} is not a directory.'
                    )
            if match := find_read.match(line):
                read = process(match[1])
                if not read.is_dir():
                    raise PathNotFound(
                        f'Read directory "{read}" in config {config} is not a directory.'
                    )
            if write and read:
                paths["WRITE_DIR"] = write
                paths["READ_DIR"] = read
                d_print(f"{write=}\n{read=}")
    raise PathNotFound("Unable to find path directives in config file:{config}")


def find_mod_folder():
    if args.mod_directory:
        mods = Path(args.mod_directory)
    else:
        mods = WRITE_DIR() / "mods"
    if not mods.is_dir():
        if mods.is_file():
            print("Mod Directory cannot be a file.")
            input("Press Enter to exit...")
            raise SystemExit
        import fa_menu

        print(f"The mod folder {mods} does not exist. Would you like to create it?")
        if not fa_menu.getAffirmation():
            raise SystemExit
        mods.mkdir(parents=True, exist_ok=True)
    paths["MODS"] = mods
    d_print(f"{mods=}")


def find_everything_else():
    paths["SAVES"] = WRITE_DIR() / "saves"

    player_data_folder = WRITE_DIR()
    if steam:
        player_data_folder = get_steam_player_data_folder()

    paths["PLAYER_DATA"] = player_data_folder / "player-data.json"
    paths["TEMP"] = WRITE_DIR() / "temp"
    paths["SCRIPT_OUTPUT"] = WRITE_DIR() / "script-output"


def get_steam_player_data_folder():
    user = os.environ["SteamAppUser"]
    steam_game_path = Path(os.getcwd())
    steam_path = steam_game_path.joinpath("..", "..", "..")
    if sys.platform == OS_flavor.WIN:
        import winreg

        key = R"SOFTWARE\WOW6432Node\Valve\Steam"
        try:
            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key)
            install_path, _ = winreg.QueryValueEx(hkey, "InstallPath")
            steam_path = Path(install_path)
            d_print("steam path updated")
        except:
            traceback.print_exc()
    steam_config = steam_path.joinpath("config", "config.vdf")
    with open(steam_config, encoding="utf8") as fp:
        for line in fp:
            if user in line:
                break
        pat = re.compile(r'\s*"?SteamID"?\s+"?(\d+)')
        for line in fp:
            if m := pat.match(line):
                steam_id = m[1]
                break
        else:
            raise ValueError(
                "Unable to find SteamID. Please report this error to Factorio Access Launcher maintainer via discord issues channel."
            )
    account_id = str(((1 << 32) - 1) & int(steam_id))
    steam_write_folder = steam_path / "userdata" / account_id / steam_game / "remote"
    steam_write_folder = steam_write_folder.resolve()
    d_print(steam_write_folder)
    return steam_write_folder
