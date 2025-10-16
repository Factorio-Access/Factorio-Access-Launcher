import subprocess
import threading
import time
import re
import os
import sys
import io
from pathlib import Path

from playsound import playsound  # cSpell: words playsound


from fa_arg_parse import launch_args, args
from save_management import save_game_rename
import launchers_mod_api



start_saving = str(Path(__file__).parent / "r/shh.wav")
save_complete = str(Path(__file__).parent / "r/shh.wav")




re_save_started = re.compile(r"Saving to _autosave\w* \(blocking\).")
re_player_join_game = re.compile(r"PlayerJoinGame .*?playerIndex\((\d+)\)")
errorA_started = re.compile(r"-+ Error -+")
errorA_end = re.compile(r"-+")
errorB_started = re.compile(r" *\d+\.\d{3} Error ")
errorB_end = re.compile(r" *\d+\.\d{3} ")


def process_game_stdout(stdout: io.BytesIO, announce_press_e, tweak_modified):
    error_buffer: list[str] | None = None
    player_index = ""
    restarting = False
    here_doc_end = None
    cmd = None
    arg = None
    for b_line in stdout:
        if b_line.startswith(b"\xef\xb7"):
            sys.stdout.buffer.write(b_line)
            sys.stdout.buffer.flush()
            continue
        try:
            line: str = b_line.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError as e:
            print(b_line)
            raise e
        if args.fa_debug:
            if args.fa_stdout_bytes:
                print(b_line)
            else:
                sys.stdout.buffer.write(b_line)
                sys.stdout.buffer.flush()
        if here_doc_end and isinstance(arg, str):
            if line == here_doc_end:
                if cmd:
                    cmd(arg)
                    cmd = None
                arg = None
                here_doc_end = None
            else:
                arg += line + "\n"
            continue
        if error_buffer is not None:
            b = errorB_end.match(line)
            if not b:
                error_buffer.append(line)
            if b or errorA_end.fullmatch(line):
                print("\n".join(error_buffer))
                launchers_mod_api.speak_interruptable_text("Printed error to console.")
                error_buffer = None
            continue

        parts = line.split(" ", 1)
        if len(parts) == 2:
            if parts[0] in launchers_mod_api.player_specific_commands:
                more_parts = parts[1].split(" ", 1)
                if not player_index or more_parts[0] == player_index:
                    cmd = launchers_mod_api.player_specific_commands[parts[0]]
                arg = more_parts[1]
            elif parts[0] in launchers_mod_api.global_commands:
                cmd = launchers_mod_api.global_commands[parts[0]]
                arg = parts[1]
            if arg:
                if arg.startswith("<<<"):
                    here_doc_end = arg[3:]
                    arg = ""
                else:
                    if cmd:
                        cmd(arg)
                    cmd = None
                    arg = None
                continue

        if line.endswith("Saving finished"):
            playsound(save_complete)
        elif re_save_started.search(line):
            playsound(start_saving)
        elif line.endswith("Restarting Factorio"):
            restarting = True
        elif line.endswith("Goodbye"):
            if not restarting:
                pass  # return
            restarting = False
        elif m := re_player_join_game.search(line):
            if not player_index:
                player_index = str(int(m[1]) + 1)
                print(f"Player index now {player_index}")
        elif "Quitting multiplayer connection." in line:
            player_index = ""
            print(f"Player index cleared")
        elif tweak_modified and "Loading map" in line:
            os.utime(tweak_modified[0], (tweak_modified[1], tweak_modified[1]))
            tweak_modified = None
        elif announce_press_e and line.endswith("Factorio initialised"):
            announce_press_e = False
            launchers_mod_api.speak_interruptable_text("Press e to continue")
        elif errorA_started.fullmatch(line) or errorB_started.match(line):
            launchers_mod_api.speak_interruptable_text(
                "Error Reported. Will print to console once game exits. Press e twice to exit and restart last save."
            )
            error_buffer = [line]


def just_launch():
    launch_with_params([], announce_press_e=True)
    return 5


def connect_to_address_menu():
    address = input("Enter the address to connect to:\n")
    return connect_to_address(address)


def connect_to_address(address):
    return launch_with_params(["--mp-connect", address])


def launch(path):
    return launch_with_params(["--load-game", path])


def launch_with_params(
    params, announce_press_e=False, save_rename=True, tweak_modified=None
):
    start_time = time.time()
    if tweak_modified:
        old_time = os.path.getmtime(tweak_modified)
        os.utime(tweak_modified, (start_time, start_time))
        tweak_modified = (tweak_modified, old_time)
    params = launch_args + params
    if "--version" in launch_args or "-v" in launch_args:
        proc = subprocess.Popen(params, stdout=sys.stdout.buffer)
        proc.wait()
        return 5
    try:
        print("Launching")
        proc = subprocess.Popen(params, stdout=subprocess.PIPE, stdin=sys.stdin.buffer)
        threading.Thread(
            target=process_game_stdout,
            args=(proc.stdout, announce_press_e, tweak_modified),
            daemon=True,
        ).start()
        proc.wait()
    except Exception as e:
        print("error running game")
        raise e
    if save_rename:
        save_game_rename(start_time)
    return 5


def time_to_exit():
    launchers_mod_api.speak_interruptable_text("Goodbye Factorio")
    time.sleep(1.5)
    raise SystemExit
